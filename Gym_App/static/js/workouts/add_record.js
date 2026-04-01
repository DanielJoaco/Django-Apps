document.addEventListener("DOMContentLoaded", () => {
  const routinesDataNode = document.getElementById("routines-data");

  const exercisesDataNode = document.getElementById("exercises-data");
  const cardioExercisesDataNode = document.getElementById(
    "cardio-exercises-data",
  );
  const stretchingExercisesDataNode = document.getElementById(
    "stretching-exercises-data",
  );

  const routineSelect = document.getElementById("id_routine_template");

  const addRoutineButton = document.getElementById("btn-add-routine-exercises");

  const manualExerciseSelect = document.getElementById("id_manual_exercise");

  const addManualButton = document.getElementById("btn-add-manual-exercise");

  const selectedList = document.getElementById("selected-exercises-list");

  const emptyMessage = document.getElementById("selected-empty-message");

  const hiddenInput = document.getElementById("selected_exercises_json");

  const saveButton = document.getElementById("btn-save-record");

  const saveWarning = document.getElementById("save-warning");

  const form = document.getElementById("add-record-form");

  const startHourSelect = document.getElementById("id_start_hour");

  const startMinuteSelect = document.getElementById("id_start_minute");

  const startPeriodSelect = document.getElementById("id_start_period");

  const endHourSelect = document.getElementById("id_end_hour");

  const endMinuteSelect = document.getElementById("id_end_minute");

  const endPeriodSelect = document.getElementById("id_end_period");

  const confirmSaveModal = document.getElementById("confirm-save-modal");

  const closeConfirmSaveButton = document.getElementById("close-confirm-save");

  const confirmSaveYesButton = document.getElementById("confirm-save-yes");

  const confirmSaveNoButton = document.getElementById("confirm-save-no");

  const warmupEnabledToggle = document.getElementById("warmup-enabled");
  const warmupIncludeCardioToggle = document.getElementById(
    "warmup-include-cardio",
  );
  const warmupIncludeStretchingToggle = document.getElementById(
    "warmup-include-stretching",
  );
  const warmupFields = document.getElementById("warmup-phase-fields");
  const warmupCardioBlock = document.getElementById("warmup-cardio-block");
  const warmupStretchingBlock = document.getElementById(
    "warmup-stretching-block",
  );
  const warmupCardioList = document.getElementById("warmup-cardio-list");
  const warmupStretchingList = document.getElementById(
    "warmup-stretching-list",
  );
  const warmupWarning = document.getElementById("warmup-warning");
  const warmupHiddenInput = document.getElementById("warmup_details_json");

  const cooldownEnabledToggle = document.getElementById("cooldown-enabled");
  const cooldownIncludeCardioToggle = document.getElementById(
    "cooldown-include-cardio",
  );
  const cooldownIncludeStretchingToggle = document.getElementById(
    "cooldown-include-stretching",
  );
  const cooldownFields = document.getElementById("cooldown-phase-fields");
  const cooldownCardioBlock = document.getElementById("cooldown-cardio-block");
  const cooldownStretchingBlock = document.getElementById(
    "cooldown-stretching-block",
  );
  const cooldownCardioList = document.getElementById("cooldown-cardio-list");
  const cooldownStretchingList = document.getElementById(
    "cooldown-stretching-list",
  );
  const cooldownWarning = document.getElementById("cooldown-warning");
  const cooldownHiddenInput = document.getElementById("cooldown_details_json");

  if (
    !routinesDataNode ||
    !exercisesDataNode ||
    !selectedList ||
    !hiddenInput
  ) {
    return;
  }

  const routines = JSON.parse(routinesDataNode.textContent);

  const exercises = JSON.parse(exercisesDataNode.textContent);
  const cardioExercises = cardioExercisesDataNode
    ? JSON.parse(cardioExercisesDataNode.textContent)
    : [];
  const stretchingExercises = stretchingExercisesDataNode
    ? JSON.parse(stretchingExercisesDataNode.textContent)
    : [];

  const routineById = new Map(
    routines.map((routine) => [String(routine.id), routine]),
  );

  const exerciseById = new Map(
    exercises.map((exercise) => [String(exercise.id), exercise]),
  );

  const selectedExercises = new Map();

  let hasUserEditedEndTime = false;

  let saveCountdownTimer = null;

  let allowFormSubmit = false;

  const buildInitialPhaseState = () => ({
    enabled: false,
    includeCardio: false,
    includeStretching: false,
    cardioEntries: new Map(
      cardioExercises.map((exercise) => [
        String(exercise.id),
        {
          exercise_id: exercise.id,
          duration_mmss: "",
          unit: "km",
          distance_value: "",
        },
      ]),
    ),
    selectedCardioIds: new Set(),
    fullBodyEntries: new Map(
      stretchingExercises.map((exercise) => [
        String(exercise.id),
        {
          exercise_id: exercise.id,
          tracking_mode: "NONE",
          duration_mmss: "",
          sets_done: "",
          reps_done: "",
        },
      ]),
    ),
    selectedFullBodyIds: new Set(),
  });

  const phaseConfigs = {
    warmup: {
      label: "calentamiento",
      toggles: {
        enabled: warmupEnabledToggle,
        cardio: warmupIncludeCardioToggle,
        stretching: warmupIncludeStretchingToggle,
      },
      fields: warmupFields,
      cardioBlock: warmupCardioBlock,
      stretchingBlock: warmupStretchingBlock,
      cardioList: warmupCardioList,
      stretchingList: warmupStretchingList,
      warning: warmupWarning,
      hiddenInput: warmupHiddenInput,
    },
    cooldown: {
      label: "cardio final",
      toggles: {
        enabled: cooldownEnabledToggle,
        cardio: cooldownIncludeCardioToggle,
        stretching: cooldownIncludeStretchingToggle,
      },
      fields: cooldownFields,
      cardioBlock: cooldownCardioBlock,
      stretchingBlock: cooldownStretchingBlock,
      cardioList: cooldownCardioList,
      stretchingList: cooldownStretchingList,
      warning: cooldownWarning,
      hiddenInput: cooldownHiddenInput,
    },
  };

  const phaseStates = {
    warmup: buildInitialPhaseState(),
    cooldown: buildInitialPhaseState(),
  };

  const setEndTimeToNow = () => {
    if (
      !endHourSelect ||
      !endMinuteSelect ||
      !endPeriodSelect ||
      hasUserEditedEndTime
    ) {
      return;
    }

    const now = new Date();

    const hours24 = now.getHours();

    const hour12 = hours24 % 12 || 12;

    const minute = String(now.getMinutes()).padStart(2, "0");

    const period = hours24 < 12 ? "AM" : "PM";

    endHourSelect.value = String(hour12);

    endMinuteSelect.value = minute;

    endPeriodSelect.value = period;
  };

  const startEndTimeAutoRefresh = () => {
    setEndTimeToNow();

    const now = new Date();

    const msUntilNextMinute =
      (60 - now.getSeconds()) * 1000 - now.getMilliseconds();

    setTimeout(
      () => {
        setEndTimeToNow();

        setInterval(setEndTimeToNow, 60000);
      },
      Math.max(msUntilNextMinute, 0),
    );
  };

  const resetSaveCountdown = () => {
    if (!confirmSaveYesButton) {
      return;
    }

    if (saveCountdownTimer) {
      clearInterval(saveCountdownTimer);

      saveCountdownTimer = null;
    }

    confirmSaveYesButton.disabled = true;

    confirmSaveYesButton.textContent = "Si (3)";
  };

  const openSaveConfirmModal = () => {
    if (!confirmSaveModal || !confirmSaveYesButton) {
      return;
    }

    confirmSaveModal.style.display = "flex";

    document.body.style.overflow = "hidden";

    resetSaveCountdown();

    let remaining = 3;

    saveCountdownTimer = setInterval(() => {
      remaining -= 1;

      if (remaining > 0) {
        confirmSaveYesButton.textContent = `Si (${remaining})`;

        return;
      }

      clearInterval(saveCountdownTimer);

      saveCountdownTimer = null;

      confirmSaveYesButton.disabled = false;

      confirmSaveYesButton.textContent = "Si";
    }, 1000);
  };

  const closeSaveConfirmModal = () => {
    if (!confirmSaveModal) {
      return;
    }

    confirmSaveModal.style.display = "none";

    document.body.style.overflow = "auto";

    resetSaveCountdown();
  };

  const buildDefaultSets = (setsCount, repsValue, tracksWeight) => {
    const count = Number.isInteger(setsCount) && setsCount > 0 ? setsCount : 1;

    const reps = Number.isInteger(repsValue) && repsValue > 0 ? repsValue : 10;

    return Array.from({ length: count }, (_, index) => ({
      set_number: index + 1,

      value: reps,

      weight: tracksWeight ? "" : null,
    }));
  };

  const syncHiddenInput = () => {
    hiddenInput.value = JSON.stringify(Array.from(selectedExercises.values()));
  };

  const parseTimeToMinutes = (hourValue, minuteValue, periodValue) => {
    const hour12 = Number(hourValue);

    const minute = Number(minuteValue);

    const period = String(periodValue || "").toUpperCase();

    if (!Number.isInteger(hour12) || hour12 < 1 || hour12 > 12) {
      return null;
    }

    if (!Number.isInteger(minute) || minute < 0 || minute > 59) {
      return null;
    }

    if (period !== "AM" && period !== "PM") {
      return null;
    }

    let hour24 = hour12 % 12;

    if (period === "PM") {
      hour24 += 12;
    }

    return hour24 * 60 + minute;
  };

  const parseMmSsToSeconds = (value) => {
    const match = String(value || "")
      .trim()
      .match(/^(\d+):([0-5]\d)$/);
    if (!match) {
      return null;
    }

    const minutes = Number(match[1]);
    const seconds = Number(match[2]);
    if (!Number.isInteger(minutes) || minutes < 0) {
      return null;
    }

    const totalSeconds = minutes * 60 + seconds;
    return totalSeconds > 0 ? totalSeconds : null;
  };

  const serializePhaseState = (phaseKey) => {
    const phaseState = phaseStates[phaseKey];
    if (!phaseState) {
      return {};
    }

    const selectedCardioEntries = [];
    phaseState.selectedCardioIds.forEach((exerciseId) => {
      const entry = phaseState.cardioEntries.get(String(exerciseId));
      if (entry) {
        selectedCardioEntries.push({
          exercise_id: entry.exercise_id,
          duration_mmss: entry.duration_mmss,
          unit: entry.unit,
          distance_value: entry.distance_value,
        });
      }
    });

    const selectedFullBodyEntries = [];
    phaseState.selectedFullBodyIds.forEach((exerciseId) => {
      const entry = phaseState.fullBodyEntries.get(String(exerciseId));
      if (entry) {
        selectedFullBodyEntries.push({
          exercise_id: entry.exercise_id,
          tracking_mode: entry.tracking_mode,
          duration_mmss: entry.duration_mmss,
          sets_done: entry.sets_done,
          reps_done: entry.reps_done,
        });
      }
    });

    return {
      enabled: phaseState.enabled,
      include_cardio: phaseState.includeCardio,
      include_stretching: phaseState.includeStretching,
      cardio_entries: selectedCardioEntries,
      full_body_entries: selectedFullBodyEntries,
    };
  };

  const syncPhaseHiddenInput = (phaseKey) => {
    const config = phaseConfigs[phaseKey];
    if (!config?.hiddenInput) {
      return;
    }
    config.hiddenInput.value = JSON.stringify(serializePhaseState(phaseKey));
  };

  const getPhaseValidationError = (phaseKey) => {
    const phaseState = phaseStates[phaseKey];
    const config = phaseConfigs[phaseKey];
    if (!phaseState || !config) {
      return null;
    }

    if (!phaseState.enabled) {
      return null;
    }

    if (!phaseState.includeCardio && !phaseState.includeStretching) {
      return `Debes elegir cardio o estiramiento en ${config.label}.`;
    }

    if (phaseState.includeCardio) {
      const selectedCardioEntries = Array.from(phaseState.selectedCardioIds)
        .map((exerciseId) => phaseState.cardioEntries.get(String(exerciseId)))
        .filter(Boolean);

      if (selectedCardioEntries.length === 0) {
        return `Debes seleccionar al menos un ejercicio de cardio en ${config.label}.`;
      }

      for (const cardioEntry of selectedCardioEntries) {
        const durationSeconds = parseMmSsToSeconds(cardioEntry.duration_mmss);
        const distanceValue = Number(cardioEntry.distance_value);

        if (cardioEntry.unit !== "steps" && cardioEntry.unit !== "km") {
          return `La unidad de cardio en ${config.label} debe ser pasos o km.`;
        }

        if (!durationSeconds) {
          return `Debes ingresar tiempo valido (mm:ss) para cardio en ${config.label}.`;
        }

        if (!Number.isFinite(distanceValue) || distanceValue <= 0) {
          return `Debes ingresar distancia valida para cardio en ${config.label}.`;
        }
      }
    }

    if (
      phaseState.includeStretching &&
      phaseState.selectedFullBodyIds.size === 0
    ) {
      return `Debes seleccionar al menos un ejercicio de estiramiento en ${config.label}.`;
    }

    if (phaseState.includeStretching) {
      const selectedFullBodyEntries = Array.from(phaseState.selectedFullBodyIds)
        .map((exerciseId) => phaseState.fullBodyEntries.get(String(exerciseId)))
        .filter(Boolean);

      for (const entry of selectedFullBodyEntries) {
        if (!["NONE", "TIME", "SETS_REPS"].includes(entry.tracking_mode)) {
          return `Modo de registro invalido en ${config.label}.`;
        }

        if (entry.tracking_mode === "TIME") {
          const durationSeconds = parseMmSsToSeconds(entry.duration_mmss);
          if (!durationSeconds) {
            return `Debes ingresar tiempo valido (mm:ss) en ejercicios de estiramiento de ${config.label}.`;
          }
        }

        if (entry.tracking_mode === "SETS_REPS") {
          const setsDone = Number(entry.sets_done);
          const repsDone = Number(entry.reps_done);
          if (
            !Number.isFinite(setsDone) ||
            setsDone <= 0 ||
            !Number.isFinite(repsDone) ||
            repsDone <= 0
          ) {
            return `Debes ingresar series y repeticiones validas en ejercicios de estiramiento de ${config.label}.`;
          }
        }
      }
    }

    return null;
  };

  const updatePhaseWarning = (phaseKey) => {
    const config = phaseConfigs[phaseKey];
    if (!config?.warning) {
      return;
    }

    const phaseError = getPhaseValidationError(phaseKey);
    if (phaseError) {
      config.warning.textContent = phaseError;
      config.warning.style.display = "block";
      return;
    }

    config.warning.textContent = "";
    config.warning.style.display = "none";
  };

  const renderPhaseCardioList = (phaseKey) => {
    const phaseState = phaseStates[phaseKey];
    const config = phaseConfigs[phaseKey];
    if (!phaseState || !config?.cardioList) {
      return;
    }

    if (cardioExercises.length === 0) {
      config.cardioList.innerHTML =
        '<p class="text-instruction">No hay ejercicios de cardio disponibles.</p>';
      return;
    }

    const optionsMarkup = cardioExercises
      .filter(
        (exercise) => !phaseState.selectedCardioIds.has(String(exercise.id)),
      )
      .map(
        (exercise) =>
          `<option value="${exercise.id}">${exercise.name} (${exercise.muscle_group})</option>`,
      )
      .join("");

    const selectedRowsMarkup = Array.from(phaseState.selectedCardioIds)
      .map((exerciseId) => {
        const exercise = cardioExercises.find(
          (item) => String(item.id) === String(exerciseId),
        );
        const entry = phaseState.cardioEntries.get(String(exerciseId));
        if (!exercise || !entry) {
          return "";
        }

        const distanceLabel =
          entry.unit === "steps" ? "Pasos" : "Distancia (km)";

        return `
          <div class="phase-cardio-row">
            <div class="form-group-inline phase-cardio-header-row">
                <div>
                    <strong>- ${exercise.name}</strong>
                    <span class="exercise-meta-text">(${exercise.muscle_group})</span>
                </div>
                <div>
                    <button type="button" class="warning-button phase-remove-item" data-phase="${phaseKey}" data-type="cardio" data-exercise-id="${exercise.id}">Quitar</button>
                </div>

            </div>

            <div class="form-group-inline phase-cardio-input-row">
              <label>Tiempo (mm:ss):</label>
              <input
                type="text"
                placeholder="mm:ss"
                class="form-control phase-cardio-duration"
                data-phase="${phaseKey}"
                data-exercise-id="${exercise.id}"
                value="${entry.duration_mmss}"
              >

              <label>${distanceLabel}:</label>
              <input
                type="number"
                min="0"
                step="0.01"
                class="form-control phase-cardio-distance"
                data-phase="${phaseKey}"
                data-exercise-id="${exercise.id}"
                value="${entry.distance_value}"
                >
                <label>Unidad:</label>
                <select
                    class="form-control phase-cardio-unit"
                    data-phase="${phaseKey}"
                    data-exercise-id="${exercise.id}"
                >
                    <option value="steps" ${entry.unit === "steps" ? "selected" : ""}>pasos</option>
                    <option value="km" ${entry.unit === "km" ? "selected" : ""}>km</option>
                </select>
            </div>
          </div>
        `;
      })
      .join("");

    config.cardioList.innerHTML = `
      <div class="form-group-inline selectior-container phase-picker-row">
        <select class="form-control phase-cardio-select-picker" data-phase="${phaseKey}">
          <option value="">Selecciona un ejercicio cardiovascular</option>
          ${optionsMarkup}
        </select>
        <button type="button" class="interactive-button phase-cardio-add-button" data-phase="${phaseKey}">Agregar cardio</button>
      </div>
      <div class="phase-selected-items">${selectedRowsMarkup}</div>
    `;

    config.cardioList
      .querySelectorAll(".phase-cardio-add-button")
      .forEach((button) => {
        button.addEventListener("click", () => {
          const select = config.cardioList.querySelector(
            `.phase-cardio-select-picker[data-phase="${phaseKey}"]`,
          );
          const exerciseId = String(select?.value || "");
          if (!exerciseId) {
            return;
          }
          phaseState.selectedCardioIds.add(exerciseId);
          renderPhaseSection(phaseKey);
          refreshSaveState();
        });
      });

    config.cardioList
      .querySelectorAll('.phase-remove-item[data-type="cardio"]')
      .forEach((button) => {
        button.addEventListener("click", () => {
          const exerciseId = String(button.dataset.exerciseId || "");
          phaseState.selectedCardioIds.delete(exerciseId);
          const entry = phaseState.cardioEntries.get(exerciseId);
          if (entry) {
            entry.duration_mmss = "";
            entry.distance_value = "";
            entry.unit = "km";
          }
          renderPhaseSection(phaseKey);
          refreshSaveState();
        });
      });

    config.cardioList
      .querySelectorAll(".phase-cardio-duration")
      .forEach((input) => {
        input.addEventListener("input", (event) => {
          const exerciseId = String(event.target.dataset.exerciseId);
          const entry = phaseState.cardioEntries.get(exerciseId);
          if (!entry) {
            return;
          }

          entry.duration_mmss = event.target.value;
          syncPhaseHiddenInput(phaseKey);
          refreshSaveState();
        });
      });

    config.cardioList
      .querySelectorAll(".phase-cardio-unit")
      .forEach((select) => {
        select.addEventListener("change", (event) => {
          const exerciseId = String(event.target.dataset.exerciseId);
          const entry = phaseState.cardioEntries.get(exerciseId);
          if (!entry) {
            return;
          }

          entry.unit = event.target.value;
          renderPhaseSection(phaseKey);
          refreshSaveState();
        });
      });

    config.cardioList
      .querySelectorAll(".phase-cardio-distance")
      .forEach((input) => {
        input.addEventListener("input", (event) => {
          const exerciseId = String(event.target.dataset.exerciseId);
          const entry = phaseState.cardioEntries.get(exerciseId);
          if (!entry) {
            return;
          }

          entry.distance_value = event.target.value;
          syncPhaseHiddenInput(phaseKey);
          refreshSaveState();
        });
      });
  };

  const renderPhaseStretchingList = (phaseKey) => {
    const phaseState = phaseStates[phaseKey];
    const config = phaseConfigs[phaseKey];
    if (!phaseState || !config?.stretchingList) {
      return;
    }

    if (stretchingExercises.length === 0) {
      config.stretchingList.innerHTML =
        '<p class="text-instruction">No hay ejercicios de estiramiento disponibles.</p>';
      return;
    }

    const optionsMarkup = stretchingExercises
      .filter(
        (exercise) => !phaseState.selectedFullBodyIds.has(String(exercise.id)),
      )
      .map(
        (exercise) =>
          `<option value="${exercise.id}">${exercise.name} (${exercise.muscle_group})</option>`,
      )
      .join("");

    const selectedRowsMarkup = Array.from(phaseState.selectedFullBodyIds)
      .map((exerciseId) => {
        const exercise = stretchingExercises.find(
          (item) => String(item.id) === String(exerciseId),
        );
        const entry = phaseState.fullBodyEntries.get(String(exerciseId));
        if (!exercise) {
          return "";
        }

        const isTimeMode = entry?.tracking_mode === "TIME";
        const isSetsRepsMode = entry?.tracking_mode === "SETS_REPS";

        return `
          <div class="phase-cardio-row">
            <div class="form-group-inline phase-stretching-row">
                <div>
                    <strong>- ${exercise.name}</strong>
                    <span class="exercise-meta-text">(${exercise.muscle_group})</span>
                </div>
                <button type="button" class="warning-button phase-remove-item" data-phase="${phaseKey}" data-type="stretching" data-exercise-id="${exercise.id}">Quitar</button>
            </div>

            <div class="form-group-inline phase-fullbody-config-row">
              <label>Modo:</label>
              <select class="form-control phase-fullbody-mode" data-phase="${phaseKey}" data-exercise-id="${exercise.id}">
                <option value="NONE" ${entry?.tracking_mode === "NONE" ? "selected" : ""}>Solo marcar</option>
                <option value="TIME" ${isTimeMode ? "selected" : ""}>Tiempo total</option>
                <option value="SETS_REPS" ${isSetsRepsMode ? "selected" : ""}>Series y repeticiones</option>
              </select>

              <div class="form-group-inline phase-fullbody-time-row" style="display: ${isTimeMode ? "flex" : "none"};">
                <label>Tiempo (mm:ss):</label>
                <input
                  type="text"
                  placeholder="mm:ss"
                  class="form-control phase-fullbody-duration"
                  data-phase="${phaseKey}"
                  data-exercise-id="${exercise.id}"
                  value="${entry?.duration_mmss || ""}"
                >
              </div>

              <div class="form-group-inline phase-fullbody-sets-row" style="display: ${isSetsRepsMode ? "flex" : "none"};">
                <label>Series:</label>
                <input
                  type="number"
                  min="1"
                  step="1"
                  class="form-control phase-fullbody-sets"
                  data-phase="${phaseKey}"
                  data-exercise-id="${exercise.id}"
                  value="${entry?.sets_done || ""}"
                >
                <label>Reps:</label>
                <input
                  type="number"
                  min="1"
                  step="1"
                  class="form-control phase-fullbody-reps"
                  data-phase="${phaseKey}"
                  data-exercise-id="${exercise.id}"
                  value="${entry?.reps_done || ""}"
                >
              </div>
            </div>
          </div>
        `;
      })
      .join("");

    config.stretchingList.innerHTML = `
      <div class="form-group-inline selectior-container phase-picker-row">
        <select class="form-control phase-stretching-select-picker" data-phase="${phaseKey}">
          <option value="">Selecciona un ejercicio de cuerpo completo</option>
          ${optionsMarkup}
        </select>
        <button type="button" class="interactive-button phase-stretching-add-button" data-phase="${phaseKey}">Agregar estiramiento</button>
      </div>
      <div class="phase-selected-items">${selectedRowsMarkup}</div>
    `;

    config.stretchingList
      .querySelectorAll(".phase-stretching-add-button")
      .forEach((button) => {
        button.addEventListener("click", () => {
          const select = config.stretchingList.querySelector(
            `.phase-stretching-select-picker[data-phase="${phaseKey}"]`,
          );
          const exerciseId = String(select?.value || "");
          if (!exerciseId) {
            return;
          }
          phaseState.selectedFullBodyIds.add(exerciseId);

          const entry = phaseState.fullBodyEntries.get(exerciseId);
          if (entry) {
            entry.tracking_mode = "NONE";
            entry.duration_mmss = "";
            entry.sets_done = "";
            entry.reps_done = "";
          }

          renderPhaseSection(phaseKey);
          refreshSaveState();
        });
      });

    config.stretchingList
      .querySelectorAll('.phase-remove-item[data-type="stretching"]')
      .forEach((button) => {
        button.addEventListener("click", () => {
          const exerciseId = String(button.dataset.exerciseId || "");
          phaseState.selectedFullBodyIds.delete(exerciseId);

          const entry = phaseState.fullBodyEntries.get(exerciseId);
          if (entry) {
            entry.tracking_mode = "NONE";
            entry.duration_mmss = "";
            entry.sets_done = "";
            entry.reps_done = "";
          }

          renderPhaseSection(phaseKey);
          refreshSaveState();
        });
      });

    config.stretchingList
      .querySelectorAll(".phase-fullbody-mode")
      .forEach((select) => {
        select.addEventListener("change", (event) => {
          const exerciseId = String(event.target.dataset.exerciseId);
          const entry = phaseState.fullBodyEntries.get(exerciseId);
          if (!entry) {
            return;
          }

          entry.tracking_mode = event.target.value;
          if (entry.tracking_mode !== "TIME") {
            entry.duration_mmss = "";
          }
          if (entry.tracking_mode !== "SETS_REPS") {
            entry.sets_done = "";
            entry.reps_done = "";
          }

          renderPhaseSection(phaseKey);
          refreshSaveState();
        });
      });

    config.stretchingList
      .querySelectorAll(".phase-fullbody-duration")
      .forEach((input) => {
        input.addEventListener("input", (event) => {
          const exerciseId = String(event.target.dataset.exerciseId);
          const entry = phaseState.fullBodyEntries.get(exerciseId);
          if (!entry) {
            return;
          }

          entry.duration_mmss = event.target.value;
          syncPhaseHiddenInput(phaseKey);
          refreshSaveState();
        });
      });

    config.stretchingList
      .querySelectorAll(".phase-fullbody-sets")
      .forEach((input) => {
        input.addEventListener("input", (event) => {
          const exerciseId = String(event.target.dataset.exerciseId);
          const entry = phaseState.fullBodyEntries.get(exerciseId);
          if (!entry) {
            return;
          }

          entry.sets_done = event.target.value;
          syncPhaseHiddenInput(phaseKey);
          refreshSaveState();
        });
      });

    config.stretchingList
      .querySelectorAll(".phase-fullbody-reps")
      .forEach((input) => {
        input.addEventListener("input", (event) => {
          const exerciseId = String(event.target.dataset.exerciseId);
          const entry = phaseState.fullBodyEntries.get(exerciseId);
          if (!entry) {
            return;
          }

          entry.reps_done = event.target.value;
          syncPhaseHiddenInput(phaseKey);
          refreshSaveState();
        });
      });
  };

  const renderPhaseSection = (phaseKey) => {
    const phaseState = phaseStates[phaseKey];
    const config = phaseConfigs[phaseKey];
    if (!phaseState || !config) {
      return;
    }

    if (config.toggles.enabled) {
      config.toggles.enabled.checked = phaseState.enabled;
    }
    if (config.toggles.cardio) {
      config.toggles.cardio.checked = phaseState.includeCardio;
    }
    if (config.toggles.stretching) {
      config.toggles.stretching.checked = phaseState.includeStretching;
    }

    if (config.fields) {
      config.fields.style.display = phaseState.enabled ? "block" : "none";
    }
    if (config.cardioBlock) {
      config.cardioBlock.style.display =
        phaseState.enabled && phaseState.includeCardio ? "block" : "none";
    }
    if (config.stretchingBlock) {
      config.stretchingBlock.style.display =
        phaseState.enabled && phaseState.includeStretching ? "block" : "none";
    }

    if (phaseState.enabled && phaseState.includeCardio) {
      renderPhaseCardioList(phaseKey);
    }
    if (phaseState.enabled && phaseState.includeStretching) {
      renderPhaseStretchingList(phaseKey);
    }

    syncPhaseHiddenInput(phaseKey);
    updatePhaseWarning(phaseKey);
  };

  const setupPhaseToggleListeners = (phaseKey) => {
    const phaseState = phaseStates[phaseKey];
    const config = phaseConfigs[phaseKey];
    if (!phaseState || !config) {
      return;
    }

    config.toggles.enabled?.addEventListener("change", (event) => {
      phaseState.enabled = event.target.checked;
      renderPhaseSection(phaseKey);
      refreshSaveState();
    });

    config.toggles.cardio?.addEventListener("change", (event) => {
      phaseState.includeCardio = event.target.checked;
      renderPhaseSection(phaseKey);
      refreshSaveState();
    });

    config.toggles.stretching?.addEventListener("change", (event) => {
      phaseState.includeStretching = event.target.checked;
      renderPhaseSection(phaseKey);
      refreshSaveState();
    });
  };

  const getFirstValidationError = () => {
    if (selectedExercises.size === 0) {
      return "Debes agregar al menos un ejercicio al registro.";
    }

    const startMinutes = parseTimeToMinutes(
      startHourSelect?.value,

      startMinuteSelect?.value,

      startPeriodSelect?.value,
    );

    const endMinutes = parseTimeToMinutes(
      endHourSelect?.value,

      endMinuteSelect?.value,

      endPeriodSelect?.value,
    );

    if (startMinutes === null || endMinutes === null) {
      return "Revisa el formato de la hora de inicio y finalizacion.";
    }

    if (endMinutes <= startMinutes) {
      return "La hora de finalizacion debe ser posterior a la hora de inicio.";
    }

    for (const exercise of selectedExercises.values()) {
      if (!exercise.tracks_weight) {
        continue;
      }

      const hasMissingWeight = exercise.sets.some((setItem) => {
        const value = String(setItem.weight ?? "").trim();

        return value === "";
      });

      if (hasMissingWeight) {
        return `Falta ingresar el peso en alguna serie de ${exercise.name}.`;
      }
    }

    const warmupValidationError = getPhaseValidationError("warmup");
    if (warmupValidationError) {
      return warmupValidationError;
    }

    const cooldownValidationError = getPhaseValidationError("cooldown");
    if (cooldownValidationError) {
      return cooldownValidationError;
    }

    return null;
  };

  const refreshSaveState = () => {
    const validationError = getFirstValidationError();

    if (saveButton) {
      saveButton.disabled = Boolean(validationError);
    }

    if (saveWarning) {
      if (validationError) {
        saveWarning.textContent = validationError;

        saveWarning.style.display = "block";
      } else {
        saveWarning.textContent = "";

        saveWarning.style.display = "none";
      }
    }

    updatePhaseWarning("warmup");
    updatePhaseWarning("cooldown");

    return validationError;
  };

  const updateEmptyState = () => {
    emptyMessage.style.display =
      selectedExercises.size === 0 ? "block" : "none";
  };

  const getSelectedExerciseFromEventTarget = (target) => {
    const li = target.closest("li[data-exercise-id]");

    if (!li) {
      return null;
    }

    const exerciseId = li.dataset.exerciseId;
    const selectedExercise = selectedExercises.get(exerciseId);

    if (!selectedExercise) {
      return null;
    }

    return { exerciseId, selectedExercise };
  };

  const renderSelectedList = () => {
    selectedList.innerHTML = "";

    selectedExercises.forEach((exercise) => {
      const li = document.createElement("li");

      li.className = "routine-add-item";

      li.dataset.exerciseId = String(exercise.id);

      const perSetLabel = exercise.is_seconds_mode
        ? "Segundos"
        : "Repeticiones";

      const setRows = exercise.sets
        .map((setItem, index) => {
          const weightMarkup = exercise.tracks_weight
            ? `

                        <input

                            type="number"

                            min="0"

                            step="0.01"

                            class="form-control set-weight-input"

                            data-set-index="${index}"

                            value="${setItem.weight ?? ""}"

                            placeholder="Peso"

                        >

                      `
            : "";

          return `

                    <div class="form-group-inline exercise-set-row" data-set-index="${index}">

                        <span>Serie ${index + 1}</span>

                        <input

                            type="number"

                            min="1"

                            class="form-control set-value-input"

                            data-set-index="${index}"

                            value="${setItem.value}"

                            placeholder="${perSetLabel}"

                        >

                        ${weightMarkup}

                        <button type="button" class="warning-button btn-remove-set btn-remove-set-size" data-set-index="${index}">- Serie</button>

                    </div>

                `;
        })
        .join("");

      const weightUnitSelector = exercise.tracks_weight
        ? `

                    <div class="form-group-inline">

                        <label for="weight-unit-${exercise.id}">Unidad de peso:</label>

                        <select id="weight-unit-${exercise.id}" class="form-control weight-unit-select">

                            <option value="kg" ${exercise.weight_unit === "kg" ? "selected" : ""}>kg</option>

                            <option value="lbs" ${exercise.weight_unit === "lbs" ? "selected" : ""}>lbs</option>

                        </select>

                    </div>

                  `
        : '<span class="text-instruction">Este ejercicio no registra peso.</span>';

      li.innerHTML = `

                <div class="exercise-item-content">

                    <strong>${exercise.name}</strong>

                    <span class="exercise-meta-text">(${exercise.muscle_group})</span>

                    <span class="exercise-meta-text"> - ${exercise.source}</span>

                    <div class="form-group-inline exercise-seconds-mode-row">

                        <label for="seconds-mode-${exercise.id}" class="exercise-seconds-mode-label">Registrar en segundos:</label>

                        <input

                            type="checkbox"

                            id="seconds-mode-${exercise.id}"

                            class="form-check-input seconds-mode-toggle"

                            ${exercise.is_seconds_mode ? "checked" : ""}

                        >

                    </div>



                    <div class="exercise-sets-container">

                        ${setRows}

                    </div>



                    <div class="form-group-inline exercise-controls">

                        <button type="button" class="success-button btn-add-set btn-add-set-size">+ Serie</button>

                        ${weightUnitSelector}

                    </div>

                </div>



                <div class="button-delete-container">

                    <button type="button" class="warning-button btn-remove-exercise btn-remove-exercise-size" data-remove-id="${exercise.id}">Quitar</button>

                </div>

            `;

      selectedList.appendChild(li);
    });

    selectedList
      .querySelectorAll("button[data-remove-id]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          const id = button.getAttribute("data-remove-id");

          selectedExercises.delete(id);

          renderSelectedList();

          syncHiddenInput();

          updateEmptyState();

          refreshSaveState();
        });
      });

    selectedList.querySelectorAll(".btn-add-set").forEach((button) => {
      button.addEventListener("click", (event) => {
        const context = getSelectedExerciseFromEventTarget(event.target);
        if (!context) {
          return;
        }
        const { selectedExercise } = context;

        const lastValue =
          selectedExercise.sets.length > 0
            ? selectedExercise.sets[selectedExercise.sets.length - 1].value
            : selectedExercise.default_value;

        selectedExercise.sets.push({
          set_number: selectedExercise.sets.length + 1,

          value: lastValue,

          weight: selectedExercise.tracks_weight ? "" : null,
        });

        renderSelectedList();

        syncHiddenInput();

        refreshSaveState();
      });
    });

    selectedList.querySelectorAll(".btn-remove-set").forEach((button) => {
      button.addEventListener("click", (event) => {
        const context = getSelectedExerciseFromEventTarget(event.target);
        if (!context) {
          return;
        }
        const { selectedExercise } = context;
        if (!selectedExercise || selectedExercise.sets.length <= 1) {
          return;
        }

        const setIndex = Number(event.target.getAttribute("data-set-index"));

        selectedExercise.sets.splice(setIndex, 1);

        selectedExercise.sets = selectedExercise.sets.map((setItem, index) => ({
          ...setItem,

          set_number: index + 1,
        }));

        renderSelectedList();

        syncHiddenInput();

        refreshSaveState();
      });
    });

    selectedList.querySelectorAll(".set-value-input").forEach((input) => {
      input.addEventListener("input", (event) => {
        const context = getSelectedExerciseFromEventTarget(event.target);
        if (!context) {
          return;
        }
        const { selectedExercise } = context;

        const setIndex = Number(event.target.getAttribute("data-set-index"));

        const newValue = Number(event.target.value);

        if (!Number.isNaN(newValue) && newValue > 0) {
          selectedExercise.sets[setIndex].value = newValue;

          syncHiddenInput();

          refreshSaveState();
        }
      });
    });

    selectedList.querySelectorAll(".set-weight-input").forEach((input) => {
      input.addEventListener("input", (event) => {
        const context = getSelectedExerciseFromEventTarget(event.target);
        if (!context) {
          return;
        }
        const { selectedExercise } = context;

        const setIndex = Number(event.target.getAttribute("data-set-index"));

        selectedExercise.sets[setIndex].weight = event.target.value;

        syncHiddenInput();

        refreshSaveState();
      });
    });

    selectedList.querySelectorAll(".weight-unit-select").forEach((select) => {
      select.addEventListener("change", (event) => {
        const context = getSelectedExerciseFromEventTarget(event.target);
        if (!context) {
          return;
        }
        const { selectedExercise } = context;

        selectedExercise.weight_unit = event.target.value;

        syncHiddenInput();

        refreshSaveState();
      });
    });

    selectedList.querySelectorAll(".seconds-mode-toggle").forEach((toggle) => {
      toggle.addEventListener("change", (event) => {
        const context = getSelectedExerciseFromEventTarget(event.target);
        if (!context) {
          return;
        }
        const { selectedExercise } = context;

        selectedExercise.is_seconds_mode = event.target.checked;

        renderSelectedList();

        syncHiddenInput();

        refreshSaveState();
      });
    });
  };

  const addExercise = (exercise, source) => {
    const key = String(exercise.id);

    if (!selectedExercises.has(key)) {
      const recommendedSets = Number(exercise.recommended_sets || 3);

      const recommendedReps = Number(exercise.recommended_reps || 10);

      const tracksWeight = Boolean(exercise.tracks_weight);

      selectedExercises.set(key, {
        id: exercise.id,

        name: exercise.name,

        muscle_group: exercise.muscle_group,

        source,

        tracks_weight: tracksWeight,

        is_seconds_mode: false,

        weight_unit: "kg",

        default_value: recommendedReps,

        sets: buildDefaultSets(recommendedSets, recommendedReps, tracksWeight),
      });

      renderSelectedList();

      syncHiddenInput();

      updateEmptyState();

      refreshSaveState();
    }
  };

  addRoutineButton?.addEventListener("click", () => {
    const routineId = routineSelect.value;

    if (!routineId) {
      return;
    }

    const routine = routineById.get(routineId);

    if (!routine) {
      return;
    }

    routine.exercises.forEach((exercise) =>
      addExercise(exercise, `Rutina: ${routine.name}`),
    );

    routineSelect.value = "";
  });

  addManualButton?.addEventListener("click", () => {
    const exerciseId = manualExerciseSelect.value;

    if (!exerciseId) {
      return;
    }

    const exercise = exerciseById.get(exerciseId);

    if (!exercise) {
      return;
    }

    addExercise(exercise, "Manual");

    manualExerciseSelect.value = "";
  });

  [endHourSelect, endMinuteSelect, endPeriodSelect].forEach((element) => {
    element?.addEventListener("change", () => {
      hasUserEditedEndTime = true;

      refreshSaveState();
    });
  });

  [startHourSelect, startMinuteSelect, startPeriodSelect].forEach((element) => {
    element?.addEventListener("change", refreshSaveState);
  });

  form?.addEventListener("submit", (event) => {
    if (allowFormSubmit) {
      return;
    }

    event.preventDefault();

    const validationError = refreshSaveState();

    if (validationError) {
      return;
    }

    openSaveConfirmModal();
  });

  closeConfirmSaveButton?.addEventListener("click", closeSaveConfirmModal);

  confirmSaveNoButton?.addEventListener("click", closeSaveConfirmModal);

  confirmSaveYesButton?.addEventListener("click", () => {
    if (!confirmSaveYesButton || confirmSaveYesButton.disabled || !form) {
      return;
    }

    allowFormSubmit = true;

    closeSaveConfirmModal();

    form.submit();
  });

  window.addEventListener("click", (event) => {
    if (event.target === confirmSaveModal) {
      closeSaveConfirmModal();
    }
  });

  setupPhaseToggleListeners("warmup");
  setupPhaseToggleListeners("cooldown");
  renderPhaseSection("warmup");
  renderPhaseSection("cooldown");

  syncHiddenInput();

  updateEmptyState();

  startEndTimeAutoRefresh();

  refreshSaveState();
});
