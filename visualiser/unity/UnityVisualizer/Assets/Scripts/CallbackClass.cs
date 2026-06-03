using Unity.VisualScripting;
using UnityEngine;

[RequireComponent(typeof(RuntimeGLTFUnzipAndApply))]
public class CallbackClass : MonoBehaviour
{
    public void CallbackMethods(GameObject obj)
    {
        Debug.Log(obj.name + " - CallbackMethods executed from CallbackClass.");
        GetComponent<ChildOutlineBuilder>().AddOutlineChild(obj);
    }
}
