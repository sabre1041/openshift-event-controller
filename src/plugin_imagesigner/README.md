# Image Signer plugin

The plugin is used to detect changes to images stored within the OpenShift Container Platform registry in order to facilitate Image Signing. Once changes to an image is detected, it is validated that it does not contain an signature. Finally, a template already present within the OpenShift cluster is instantiated to perform further actions (such as signing the image).


## Configuration

### Global Config Options

| Environment Variable | ini Variable | Required | Description |
| ------------- | ------------- | -------| --------- |
| K8S_API_ENDPOINT | k8s_api_endpoint | True | OpenShift/Kubernetes API hostname:port |
| K8S_TOKEN  | k8s_token | True; will be pulled from Pod | Login token (`oc whoami -t`) |
| K8S_NAMESPACED | k8s_namespaced | False | Whether the resource is namespace scoped |
| K8S_NAMESPACE | k8s_namespace | When `K8S_NAMESPACED` is `True`; will be pulled from Pod | Namespace you want to listen watch resources in |
| K8S_API_PATH | k8s_api_path | False | The full API resource path. Override API path construction based on other values |
| K8S_API_GROUP | k8s_api_group | False | Kubernetes API group |
| K8S_API_VERSION | k8s_api_version | False | Kubernetes API Version |
| K8S_RESOURCE | k8s_resource | True | The `Kind` of the Kubernetes or OpenShift resource |
| K8S_CA | k8s_ca | False; will be pulled from Pod | Path to the `ca.crt` file for the cluster |
| LOG_LEVEL | log_level | False | Logging threshold to be output. Options: DEBUG, INFO, WARNING, ERROR, CRITICAL; Default: INFO
| WATCHER_PLUGIN | watcher_plugin | False | Name of the Plugin you want to run in the Watcher. Default: 'simple' |


### Image Signer Plugin Configuration Options

| ini Variable | Required | Description |
| ------------- | ------------- | ------------- |
| registries | True | Comma separated list of registries to consider for image signing. `*` can be used to indicate all registries should be considered |
| imagesigner_annotation | True | Annotation to place on images managed by this plugin |
| template_name | True | Name of the template instantiated to trigger signing actions |
| signer_identity | True | Signer identity used to sign the image |

