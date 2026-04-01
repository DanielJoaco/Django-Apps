document.addEventListener("DOMContentLoaded", () => {
  const routinesDataNode = document.getElementById("routines-data");

  const exercisesDataNode = document.getElementById("exercises-data");

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

  syncHiddenInput();

  updateEmptyState();

  startEndTimeAutoRefresh();

  refreshSaveState();
});
