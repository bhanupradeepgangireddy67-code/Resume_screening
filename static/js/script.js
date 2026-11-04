/**
 * Frontend JavaScript Interactions
 * Handles UI helpers, confirmation dialogs, file upload UX, and dynamic status updates.
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Confirm Delete Handlers
  const deleteButtons = document.querySelectorAll(".btn-confirm-delete");
  deleteButtons.forEach(button => {
    button.addEventListener("click", function (event) {
      const message = this.getAttribute("data-confirm-message") || "Are you sure you want to delete this item? This action cannot be undone.";
      if (!confirm(message)) {
        event.preventDefault();
      }
    });
  });

  // 2. Resume File Upload UI Feedback
  const fileInput = document.getElementById("resume_file");
  const fileNameDisplay = document.getElementById("file-name-display");
  const dropzone = document.querySelector(".upload-dropzone");

  if (fileInput && dropzone) {
    // Click trigger on dropzone
    dropzone.addEventListener("click", () => fileInput.click());

    // Drag-and-drop visual indicators
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.style.borderColor = '#1d4ed8';
        dropzone.style.backgroundColor = '#dbeafe';
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.style.borderColor = '#93c5fd';
        dropzone.style.backgroundColor = '#f0f7ff';
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        fileInput.files = files;
        updateFileDisplay(files[0]);
      }
    });

    fileInput.addEventListener("change", function () {
      if (this.files.length > 0) {
        updateFileDisplay(this.files[0]);
      }
    });

    function updateFileDisplay(file) {
      if (fileNameDisplay) {
        fileNameDisplay.innerHTML = `
          <div class="alert alert-success d-inline-block py-2 px-3 mt-3 mb-0">
            <i class="bi bi-file-earmark-check"></i> Selected: <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)
          </div>
        `;
      }
    }
  }

  // 3. Login password visibility toggle
  const passwordInput = document.getElementById("password");
  const passwordToggle = document.getElementById("toggle-password");

  if (passwordInput && passwordToggle) {
    passwordToggle.addEventListener("click", () => {
      const isVisible = passwordInput.type === "text";
      passwordInput.type = isVisible ? "password" : "text";
      passwordToggle.setAttribute("aria-pressed", String(!isVisible));
      passwordToggle.setAttribute("aria-label", isVisible ? "Show password" : "Hide password");
      passwordToggle.innerHTML = `<i class="bi ${isVisible ? "bi-eye" : "bi-eye-slash"}" aria-hidden="true"></i>`;
    });
  }

  // 4. Interview Type Toggle: toggle meeting link requirement
  const interviewTypeSelect = document.getElementById("interview_type");
  const meetingLinkGroup = document.getElementById("meeting-link-group");
  const meetingLinkInput = document.getElementById("meeting_link");

  if (interviewTypeSelect && meetingLinkGroup) {
    const handleInterviewType = () => {
      if (interviewTypeSelect.value === "Online") {
        meetingLinkGroup.style.display = "block";
        if (meetingLinkInput) meetingLinkInput.placeholder = "e.g., https://meet.google.com/xyz or Zoom link";
      } else {
        meetingLinkGroup.style.display = "block";
        if (meetingLinkInput) meetingLinkInput.placeholder = "e.g., Office Room 402, Building A (Optional)";
      }
    };
    interviewTypeSelect.addEventListener("change", handleInterviewType);
    handleInterviewType();
  }

  // 5. Auto-hide flash alerts after 6 seconds
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach(alert => {
    setTimeout(() => {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {
        alert.style.display = "none";
      }
    }, 6000);
  });
});
