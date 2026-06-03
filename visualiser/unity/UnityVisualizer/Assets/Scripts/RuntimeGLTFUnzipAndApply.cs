using UnityEngine;
using UnityGLTF;
using UnityGLTF.Loader;
using System.Threading.Tasks;
using System.IO;
using UnityEngine.Networking;
using System.IO.Compression;

[RequireComponent(typeof(ServerStatusChecker))]
[RequireComponent(typeof(CallbackClass))]
public class RuntimeGLTFUnzipAndApply : MonoBehaviour
{
    [SerializeField] GameObject parentObject;

    [Header("Concept Input")]
    [SerializeField] private string conceptName;  // <-- set this from another script or inspector

    private string glbZipUrl = "";
    private string unzipFolder;
    private string zipPath;

    // Public entrypoint, called externally
    public async void Spawner(string concept = null, Vector3 position = default, Quaternion rotation = default)
    {
        string glbZipUrlServer = GetComponent<ServerStatusChecker>().serverUrl;
        glbZipUrl = glbZipUrlServer + "process-3d-file";
        if (string.IsNullOrEmpty(glbZipUrlServer))
        {
            Debug.LogError("Server URL is empty. Please set it in the ServerStatusChecker component.");
            return;
        }
        unzipFolder = Path.Combine(Application.persistentDataPath, "UnzippedGLB");

        if (!string.IsNullOrEmpty(concept))
            conceptName = concept;

        if (string.IsNullOrEmpty(conceptName))
        {
            Debug.LogError("Concept name not set. Cannot request model.");
            return;
        }

        await DownloadUnzipAndInstantiate(position, rotation);
    }

    async Task DownloadUnzipAndInstantiate(Vector3 position, Quaternion rotation)
    {
        Debug.Log($"Starting download for concept '{conceptName}'...");
        zipPath = Path.Combine(Application.persistentDataPath, "model.zip");

        // Build POST request with form data
        WWWForm form = new WWWForm();
        form.AddField("concept", conceptName);

        UnityWebRequest www = UnityWebRequest.Post(glbZipUrl, form);
        www.downloadHandler = new DownloadHandlerFile(zipPath);

        await www.SendWebRequest();

        Debug.Log("Download completed with response code: " + www.responseCode);

#if UNITY_2020_1_OR_NEWER
        if (www.result != UnityWebRequest.Result.Success)
#else
        if (www.isNetworkError || www.isHttpError)
#endif
        {
            Debug.LogError($"ZIP download failed ({www.responseCode}): {www.error}");
            return;
        }

        if (Directory.Exists(unzipFolder))
            Directory.Delete(unzipFolder, true);

        try
        {
            ZipFile.ExtractToDirectory(zipPath, unzipFolder);
            Debug.Log("Unzipped to: " + unzipFolder);
        }
        catch (System.Exception ex)
        {
            Debug.LogError("Failed to unzip file: " + ex.Message);
            return;
        }

        await LoadGLB(unzipFolder, position, rotation);
    }

    async Task LoadGLB(string unzipFolder, Vector3 position, Quaternion rotation)
    {
        var glbFiles = Directory.GetFiles(unzipFolder, "*.glb", SearchOption.AllDirectories);
        if (glbFiles.Length == 0)
        {
            Debug.LogError("No GLB found in unzipped folder.");
            return;
        }
        string glbPath = glbFiles[0];

        var textureFiles = Directory.GetFiles(unzipFolder, "*.png", SearchOption.AllDirectories);
        string texturePath = textureFiles.Length > 0 ? textureFiles[0] : null;

        if (!File.Exists(glbPath))
        {
            Debug.LogError("GLB file not found: " + glbPath);
            return;
        }

        string basePath = Path.GetDirectoryName(glbPath);
        var loader = new FileLoader(basePath);
        AsyncCoroutineHelper coroutineHelper = gameObject.AddComponent<AsyncCoroutineHelper>();
        CallbackClass callbackClass = GetComponent<CallbackClass>();

        var importOptions = new ImportOptions
        {
            DataLoader = loader,
            AsyncCoroutineHelper = coroutineHelper
        };

        string fileName = Path.GetFileName(glbPath);
        Transform glbRoot = new GameObject("GLB_Instance").transform;
        if (parentObject != null)
            glbRoot.SetParent(parentObject.transform);
        glbRoot.position = position;
        glbRoot.rotation = rotation;

        var gltfImporter = new GLTFSceneImporter(fileName, importOptions)
        {
            SceneParent = glbRoot
        };

        try
        {
            await gltfImporter.LoadSceneAsync();
            await Task.Yield();

            Debug.Log("GLB import finished. Child count: " + glbRoot.childCount);

            if (!string.IsNullOrEmpty(texturePath))
            {
                Texture2D loadedTexture = LoadTextureFromFile(texturePath);
                if (loadedTexture != null)
                {
                    Material newMat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                    newMat.mainTexture = loadedTexture;

                    var renderers = glbRoot.GetComponentsInChildren<Renderer>();
                    Debug.Log("Renderer count: " + renderers.Length);

                    foreach (Renderer r in renderers)
                        if (r != null) r.material = newMat;
                }
            }
            var meshFilter = glbRoot.GetComponentInChildren<MeshFilter>();
            if (meshFilter != null)
            {
                var collider = glbRoot.gameObject.AddComponent<MeshCollider>();
                collider.sharedMesh = meshFilter.sharedMesh;
            }

            callbackClass.CallbackMethods(glbRoot.gameObject);
        }
        catch (System.Exception e)
        {
            Debug.LogError("Error loading GLB: " + e.Message);
        }
    }

    Texture2D LoadTextureFromFile(string texturePath)
    {
        if (!File.Exists(texturePath))
        {
            Debug.LogError("Texture file not found: " + texturePath);
            return null;
        }

        byte[] fileData = File.ReadAllBytes(texturePath);
        Texture2D tex = new Texture2D(2, 2);
        if (tex.LoadImage(fileData))
            return tex;

        return null;
    }

    private void OnDestroy()
    {
        if (Directory.Exists(unzipFolder))
            Directory.Delete(unzipFolder, true);
    }
}
