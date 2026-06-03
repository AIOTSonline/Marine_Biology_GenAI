using UnityEngine;

public class ChildOutlineBuilder : MonoBehaviour
{
    [SerializeField] string ChildName;
    [SerializeField] Material OutlineMaterial;
    
    private GameObject lastSpawnedObject;
    public void AddOutlineChild(GameObject obj)
    {
        GameObject child = new GameObject();
        child.name = ChildName;
        child.AddComponent<MeshFilter>();
        child.GetComponent<MeshFilter>().mesh = obj.GetComponent<MeshCollider>().sharedMesh;

        child.AddComponent<MeshRenderer>();
        child.GetComponent<MeshRenderer>().material = OutlineMaterial;
        child.SetActive(false);
        Instantiate(child, obj.transform);
    }
}
