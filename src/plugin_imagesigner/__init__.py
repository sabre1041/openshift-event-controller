import traceback, sys, os, requests, json, subprocess

def handle_event(watcher, event, config):

    response_msg = ""

    if event['type'] == 'ADDED' or event['type'] == 'MODIFIED':
        if need_signature(event, config, watcher.logger):

            template_result = instantiate_template(event, config, watcher.logger, watcher)

            if template_result is None:
                response_msg = "Signature Not Needed"
            elif template_result:
                update_image_result = update_image(event['object']['metadata']['name'], config, watcher)

                if update_image_result:
                    response_msg = "Signature Build Triggered"
                else:
                    response_msg = "Signature Build Trigger But Image Update Failed"
            else:
                response_msg = "Signature Build Triggered Failed"
        else:
            response_msg = "Signature Not Needed"

    message = "Kind: {0}; Name: {1}; Event Type: {2}; Message: {3}".format(event['object']['kind'], event['object']['metadata']['name'], event['type'], response_msg)
    log_level = config.get('message_log_level','INFO')
    return message, log_level

# Check if an signature signing action should be triggered
def need_signature(event, config, logger):
    
    if not check_image_annotation(event, config, logger):
        if check_image_registry(event, config, logger):
            if not check_has_image_signature(event, logger):
                logger.debug("Image Signature Annotation Not Present")
                return True
    else:
        logger.debug("Image Has Signature Annotation Present. Ignoring")
    
    return False

# Check if image has Annotation
def check_image_annotation(event, config, logger):
    
    try:    
        image_annotation = get_image_signer_annotation(config)
        
        if event['object']['metadata']['annotations'][image_annotation]:
            return True
        else:
            return False
    except KeyError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.debug("Error message: {0}".format(repr(traceback.format_exception(exc_type, exc_value, exc_traceback,
                            limit=2))))
        logger.debug("Got an event with no annotation: {0}".format(event))
    
    return False

# Check if the image in registry that should be signed
def check_image_registry(event, config, logger):

    registries = config.get('registries')
    registry_list = registries.split(',')

    image_reference = event['object']['dockerImageReference']

    image_registry = image_reference.rsplit('/')[0]

    if "*" in registry_list or image_registry in registry_list:
        logger.debug("Image Registry Valid for Signing: {0}".format(image_registry))
        return True

    logger.debug("Image Registry Not Valid for Signing: {0}".format(image_registry))
    return False

# Check if the image already has existing signatures
def check_has_image_signature(event, logger):
    
    if 'signatures' in event['object'] and isinstance(event['object']['signatures'], list) and len(event['object']['signatures']) > 0:
        logger.debug("Image Already Has Signatures")
        return True

    logger.debug("Image Already Has Signatures")
    return False
        
# Instantiate the Template
def instantiate_template(event, config, logger, watcher):
    
    image_reference = event['object']['dockerImageReference']


    # Need to determine the image tag and digest
    image_components = image_reference.rsplit('/')

    image_namespace = image_components[1]

    image_name = image_components[2].rsplit("@")[0]

    image_digest = image_components[2].rsplit("@")[1]

    tag_located, tag = locate_tag(image_reference, image_namespace, image_name, watcher.logger, watcher)

    if not tag_located:
        return

    ## Required Parameters
    signer_identity = config.get('signer_identity')

    ## Optional Parameters
    gpg_secret = config.get('gpg_secret')
    serviceaccount_name = config.get('serviceaccount_name')
    node_selector_key = config.get('node_selector_key')
    node_selector_value = config.get('node_selector_value')
    
    process_cmd = ['oc', 'process', '-n', watcher.config.k8s_namespace, config.get('template_name')]

    build_parameters(process_cmd,"IMAGE_TO_SIGN", "{0}:{1}".format(image_reference.rsplit("@")[0], tag))
    build_parameters(process_cmd,"IMAGE_DIGEST", image_digest)
    build_parameters(process_cmd,"SERVICE_ACCOUNT_NAME", serviceaccount_name)
    build_parameters(process_cmd,"SIGN_BY", signer_identity)
    build_parameters(process_cmd,"GPG_SECRET", gpg_secret)
    build_parameters(process_cmd,"NODE_SELECTOR_KEY", node_selector_key)
    build_parameters(process_cmd,"NODE_SELECTOR_VALUE", node_selector_value)

    p1 = subprocess.Popen(process_cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['oc', 'apply', '-n', watcher.config.k8s_namespace, '-f-'], stdin=p1.stdout, stdout=subprocess.PIPE)
    output,err = p2.communicate()

    return True if p2.returncode == 0 else False


def locate_tag(image_reference, image_namespace, image_name, logger, watcher):
    
    req = requests.get("https://{0}/oapi/v1/namespaces/{1}/imagestreams/{2}".format(watcher.config.k8s_endpoint, image_namespace, image_name),
                               headers={'Authorization': 'Bearer {0}'.format(watcher.config.k8s_token)},
                               params="", verify=watcher.config.k8s_ca)
    
    if req.status_code == 200:
        is_json = json.loads(req.text)

        try:
            if is_json['status']['tags']:
                for tag in is_json['status']['tags']:
                    # We are only concerned with the most recent value
                    if len(tag['items']) > 0:
                        tag_item = tag['items'][0]

                        if image_reference == tag_item['dockerImageReference']:
                            return True, tag['tag']

        except KeyError:
            logger.debug("Unable to locate tags of image {0} in namespace {1}".format(image_name, image_namespace))
        
    return False, ''
    

def update_image(image_digest, config, watcher):

    req = requests.patch('https://{0}/oapi/v1/images/{1}'.format(watcher.config.k8s_endpoint, image_digest),
                        headers={'Authorization': 'Bearer {0}'.format(watcher.config.k8s_token), 'Content-Type':'application/strategic-merge-patch+json'},
                        data=json.dumps({'metadata': {'annotations': {'{0}'.format(get_image_signer_annotation(config)): 'true'}}}),
                        params="", verify=watcher.config.k8s_ca)
    
    return True if req.status_code == 200 else False

def build_parameters(cmd, parameter_name, parameter):
    
    if parameter:
        cmd.append("-p")
        cmd.append("{0}={1}".format(parameter_name, parameter))

def get_image_signer_annotation(config):
    return config.get('imagesigner_annotation') if config.get('imagesigner_annotation') else "openshift.io/image-signer"