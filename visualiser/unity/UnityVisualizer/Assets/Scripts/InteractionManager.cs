using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Camera))]
public class InteractionManager : MonoBehaviour
{
    [Header("Camera Settings")]
    [SerializeField] private float rotationSpeed = 100f;
    [SerializeField] private float zoomSpeed = 10f;
    [SerializeField] private float panSpeed = 0.5f;

    [Header("Outline Child")]
    [Tooltip("Optional: if set, we'll prefer a child with this substring in its name (e.g. 'Outline').")]
    [SerializeField] private string outlineChildNameHint = "Outline";

    private Camera cam;
    private Controls controls;

    // Hover state
    private Transform hoveredObject;
    private GameObject hoveredOutlineChild;

    private GameObject duplicateObject;
    private float duplicateDistanceFromCamera = 0f;  
    [SerializeField] private Transform duplicateParent;

    public Vector3 pivotPoint = Vector3.zero;

    void Awake()
    {
        cam = Camera.main;
        controls = new Controls();
    }

    void OnEnable()  => controls.Enable();
    void OnDisable() => controls.Disable();

    void Update()
    {
        HandleCamera();
        HandleHoverAndObjects();
    }

    void HandleCamera()
    {
        Vector2 look   = controls.Camera.Look.ReadValue<Vector2>();
        Vector2 scroll = controls.Camera.Zoom.ReadValue<Vector2>();

        if (controls.Camera.Rotate.IsPressed())
        {
            transform.RotateAround(pivotPoint, Vector3.up,   look.x * rotationSpeed * Time.deltaTime);
            transform.RotateAround(pivotPoint, transform.right, -look.y * rotationSpeed * Time.deltaTime);
        }

        if (controls.Camera.Pan.IsPressed())
        {
            Vector3 delta = new Vector3(-look.x * panSpeed * Time.deltaTime, -look.y * panSpeed * Time.deltaTime, 0);
            transform.Translate(delta, Space.Self);
            pivotPoint += transform.TransformDirection(delta);
        }

        if (Mathf.Abs(scroll.y) > 0.01f)
        {
            Vector3 move = transform.forward * scroll.y * zoomSpeed * Time.deltaTime;
            transform.position += move;
            pivotPoint += move;
        }
    }

    void HandleHoverAndObjects()
    {
        Ray ray = cam.ScreenPointToRay(Mouse.current.position.ReadValue());

        if (Physics.Raycast(ray, out RaycastHit hit))
        {
            Transform hitObj = hit.transform;

            if (hoveredObject != hitObj)
            {
                HideHoveredOutline();     
                hoveredObject = hitObj;
                hoveredOutlineChild = FindOutlineChild(hoveredObject);

                if (hoveredOutlineChild != null)
                    hoveredOutlineChild.SetActive(true);
            }

            if (controls.Object.Duplicate.WasPressedThisFrame())
            {
                duplicateObject = Instantiate(hitObj.gameObject, parent: duplicateParent);

                DisableAllOutlineChildren(duplicateObject.transform);

                duplicateDistanceFromCamera = Vector3.Distance(cam.transform.position, hitObj.position);

                Vector3 startPos = ray.origin + ray.direction * duplicateDistanceFromCamera;
                duplicateObject.transform.position = startPos;
                duplicateObject.transform.rotation = hitObj.rotation; // preserve rotation
            }

            if (duplicateObject != null)
            {
                Vector3 followPos = ray.origin + ray.direction * duplicateDistanceFromCamera;
                duplicateObject.transform.position = followPos;

                if (controls.Object.Place.WasPressedThisFrame())
                {
                    duplicateObject = null; 
                }
            }
        }
        else
        {
            HideHoveredOutline();
        }
    }

    GameObject FindOutlineChild(Transform root)
    {
        if (!string.IsNullOrEmpty(outlineChildNameHint))
        {
            foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
            {
                if (t == root) continue;
                if (t.name.ToLower().Contains(outlineChildNameHint.ToLower()))
                    return t.gameObject;
            }
        }

        foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
        {
            if (r.transform == root) continue;
            bool looksLikeOverlay =
                r.shadowCastingMode == UnityEngine.Rendering.ShadowCastingMode.Off ||
                (r.sharedMaterial != null && r.sharedMaterial.renderQueue >= 3000);

            if (looksLikeOverlay)
                return r.gameObject;
        }

        return null;
    }

    void HideHoveredOutline()
    {
        if (hoveredOutlineChild != null)
        {
            hoveredOutlineChild.SetActive(false);
            hoveredOutlineChild = null;
        }
        hoveredObject = null;
    }

    void DisableAllOutlineChildren(Transform root)
    {
        foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
        {
            if (t == root) continue;
            if (!string.IsNullOrEmpty(outlineChildNameHint) && t.name.ToLower().Contains(outlineChildNameHint.ToLower()))
            {
                t.gameObject.SetActive(false);
                continue;
            }

            var r = t.GetComponent<MeshRenderer>();
            if (r != null && (r.sharedMaterial != null && r.sharedMaterial.renderQueue >= 3000))
            {
                t.gameObject.SetActive(false);
            }
        }
    }
}
