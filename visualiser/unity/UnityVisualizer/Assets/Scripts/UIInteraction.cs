using TMPro;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.InputSystem;
using UnityEngine.EventSystems;
using System.Collections.Generic;
using System.Collections;

public class UIInteraction : MonoBehaviour
{
    [SerializeField] private GameObject welcomePanel;
    [SerializeField] private GameObject tutorialPanel;
    [SerializeField] private GameObject settingsPanel;

    [SerializeField] private Button lightButton;
    [SerializeField] private Image lightOnImage;
    [SerializeField] private Image lightOffImage;
    [SerializeField] private Button hintButton;
    [SerializeField] private Button settingButton;

    [Header("Spawn Input UI")]
    [SerializeField] private TMP_InputField spawnInputField;
    [SerializeField] private Button spawnSubmitButton;

    [Header("Server Input UI")]
    [SerializeField] private TMP_InputField serverInputField;
    [SerializeField] private Button serverSubmitButton;

    [SerializeField] private Light helperLight;

    private bool lightOn = true;
    private List<Button> allButtons = new List<Button>();

    private float panelCooldown = 0.1f; // Added to avoid double toggles
    private float lastTutorialCloseTime = -1f;
    private float lastSettingsCloseTime = -1f;

    private Camera mainCamera;

    void Start()
    {
        if (welcomePanel) welcomePanel.SetActive(true);
        if (tutorialPanel) tutorialPanel.SetActive(false);
        if (settingsPanel) settingsPanel.SetActive(false);
        if (lightButton) lightButton.gameObject.SetActive(false);
        if (hintButton) hintButton.gameObject.SetActive(false);
        if (settingButton) settingButton.gameObject.SetActive(false);
        if (spawnSubmitButton) spawnSubmitButton.gameObject.SetActive(false);
        if (spawnInputField) spawnInputField.gameObject.SetActive(false);

        if (lightButton) lightButton.onClick.AddListener(ToggleLight);
        if (hintButton) hintButton.onClick.AddListener(ShowTutorial);
        if (settingButton) settingButton.onClick.AddListener(OpenSettings);

        if (spawnSubmitButton) spawnSubmitButton.onClick.AddListener(OnSpawnSubmit);
        if (serverSubmitButton) serverSubmitButton.onClick.AddListener(OnServerSubmit);

        lightOn = true;
        if (helperLight) helperLight.enabled = true;
        UpdateLightUI();

        if (lightButton) allButtons.Add(lightButton);
        if (hintButton) allButtons.Add(hintButton);
        if (settingButton) allButtons.Add(settingButton);

        mainCamera = Camera.main;
    }

    void Update()
    {
        if (Keyboard.current != null)
        {
            if (Keyboard.current.enterKey.wasPressedThisFrame || Keyboard.current.spaceKey.wasPressedThisFrame)
            {
                if (welcomePanel.activeSelf) CloseWelcome();
                else if (tutorialPanel.activeSelf) HideTutorial();
                else if (settingsPanel.activeSelf) CloseSettings();
            }
        }

        if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame)
        {
            if (welcomePanel.activeSelf && !IsPointerOverUI(welcomePanel)) CloseWelcome();
            else if (tutorialPanel.activeSelf && !IsPointerOverUI(tutorialPanel)) HideTutorial();
            else if (settingsPanel.activeSelf && !IsPointerOverUI(settingsPanel)) CloseSettings();
        }
    }

    private void ToggleLight()
    {
        lightOn = !lightOn;
        if (helperLight) helperLight.enabled = lightOn;
        UpdateLightUI();
    }

    private void UpdateLightUI()
    {
        if (lightOnImage) lightOnImage.enabled = lightOn;
        if (lightOffImage) lightOffImage.enabled = !lightOn;
    }

    private void ShowTutorial()
    {
        if (tutorialPanel.activeSelf) return;
        if (Time.time - lastTutorialCloseTime < panelCooldown) return;

        tutorialPanel.SetActive(true);
        BlockAllButtons(true);
    }

    private void HideTutorial()
    {
        if (!tutorialPanel.activeSelf) return;
        tutorialPanel.SetActive(false);
        StartCoroutine(UnlockButtonsWithDelay());
        lastTutorialCloseTime = Time.time;
    }

    private void CloseWelcome()
    {
        if (!welcomePanel.activeSelf) return;
        welcomePanel.SetActive(false);

        if (lightButton) lightButton.gameObject.SetActive(true);
        if (hintButton) hintButton.gameObject.SetActive(true);
        if (settingButton) settingButton.gameObject.SetActive(true);
        if (spawnSubmitButton) spawnSubmitButton.gameObject.SetActive(true);
        if (spawnInputField) spawnInputField.gameObject.SetActive(true);
        
        StartCoroutine(UnlockButtonsWithDelay());
    }

    private void OpenSettings()
    {
        if (settingsPanel.activeSelf) return;
        if (Time.time - lastSettingsCloseTime < panelCooldown) return;

        settingsPanel.SetActive(true);
        BlockAllButtons(true);
    }

    private void CloseSettings()
    {
        if (!settingsPanel.activeSelf) return;
        settingsPanel.SetActive(false);
        StartCoroutine(UnlockButtonsWithDelay());
        lastSettingsCloseTime = Time.time;
    }

    private void OnSpawnSubmit()
    {
        if (!spawnInputField) return;
        string value = spawnInputField.text.Trim();
        Debug.Log("Spawn submitted: " + value);

        Vector3 pivot = mainCamera.GetComponent<InteractionManager>().pivotPoint;
        GetComponent<RuntimeGLTFUnzipAndApply>().Spawner(value, pivot, Quaternion.LookRotation(mainCamera.transform.position - pivot));
        spawnInputField.text = string.Empty;
    }

    private void OnServerSubmit()
    {
        if (!serverInputField) return;
        string value = serverInputField.text.Trim();
        Debug.Log("Server submitted: " + value);

        GetComponent<ServerStatusChecker>().SetServerUrl(value);
    }

    private bool IsPointerOverUI(GameObject panel)
    {
        if (!panel) return false;
        PointerEventData eventData = new PointerEventData(EventSystem.current);
        eventData.position = Mouse.current.position.ReadValue();
        var results = new List<RaycastResult>();
        EventSystem.current.RaycastAll(eventData, results);
        foreach (var r in results)
            if (r.gameObject == panel || r.gameObject.transform.IsChildOf(panel.transform))
                return true;
        return false;
    }

    public void BlockAllButtons(bool block)
    {
        foreach (var btn in allButtons)
        {
            if (!btn) continue;
            btn.interactable = !block;
        }
    }

    private IEnumerator UnlockButtonsWithDelay()
    {
        yield return new WaitForSeconds(panelCooldown);
        BlockAllButtons(false);
    }
}
