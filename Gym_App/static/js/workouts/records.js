document.addEventListener("DOMContentLoaded", () => {
  const addRecordButton = document.getElementById("add-record-entry-button");
  if (!addRecordButton) {
    return;
  }

  const LOCAL_DRAFT_KEY = "gym_app_add_record_draft";

  try {
    const rawDraft = localStorage.getItem(LOCAL_DRAFT_KEY);
    if (!rawDraft) {
      return;
    }

    const parsedDraft = JSON.parse(rawDraft);
    if (parsedDraft && parsedDraft.session_active === true) {
      addRecordButton.textContent = "Continuar con Registro";
    }
  } catch {
    // Keep default button text if local storage cannot be parsed.
  }
});
