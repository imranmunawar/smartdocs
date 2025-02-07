$(document).ready(function () {
  // Calling section progress on load to set for all the pages
  setAllsectionProgressMarker();
  setSidebarProgressMarkers();
  setSectionProgressElements();

  function setSectionProgressElements() {
    var label = document.querySelector(".progress_label");
    var subsectionId = label.id;
    if (subsectionId) {
      var documentId = $(".page-wrapper").data("document-id");
      var elements_url =
        "/get_subsection_progress/" + subsectionId + "/" + documentId;
      $.ajax({
        type: "GET",
        url: elements_url,
        success: function (response) {
          document.getElementById("answered_questions").innerText =
            response.answered_question;
          document.getElementById("total_questions").innerText =
            response.total_questions;
          label.style.display = "block";
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    }
  }

  function setAllsectionProgressMarker() {
    //Gets the section progress for all sections in a page

    var divs = document.querySelectorAll(".s_sections");
    var documentId = $(".page-wrapper").data("document-id");
    divs.forEach(function (div) {
      var sectionId = div.id;
      var section_progress_url =
        "/get_section_progress/" + sectionId + "/" + documentId;
      sectionProgressMarker(section_progress_url, sectionId);
    });
  }

  function setSidebarProgressMarkers() {
    $(".s_check").each(function () {
      var documentId = $(".page-wrapper").data("document-id");
      var sectionId = $(this).data("section-id");
      var section_progress_url =
        "/get_section_progress/" + sectionId + "/" + documentId;
      $.ajax({
        type: "GET",
        url: section_progress_url,
        success: function (response) {
          if (response.progress) {
            $("#" + "sidebar-check-" + sectionId)
              .attr("hidden", false)
              .removeClass("fa-exclamation-circle")
              .addClass("fa-check-circle");

            $("#" + "sidebar-check-" + sectionId).removeClass("icon-red");

            $("#" + "sidebar-check-" + sectionId).addClass("icon-green");
          } else {
            $("#" + "sidebar-check-" + sectionId)
              .attr("hidden", false)
              .removeClass("fa-check-circle")
              .addClass("fa-exclamation-circle");

            $("#" + "sidebar-check-" + sectionId).removeClass("icon-green");

            $("#" + "sidebar-check-" + sectionId).addClass("icon-red");
          }
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    });
    $(".ps_section").each(function () {
      var documentId = $(".page-wrapper").data("document-id");
      var sectionId = $(this).data("parent-section-id");
      var section_progress_url =
        "/get_parent_section_progress/" + sectionId + "/" + documentId;
      $.ajax({
        type: "GET",
        url: section_progress_url,
        success: function (response) {
          if (response.progress) {
            $("#" + "parent-sidebar-check-" + sectionId).removeClass(
              "fa-exclamation-circle"
            );
            $("#" + "parent-sidebar-check-" + sectionId).removeClass(
              "icon-red"
            );
            $("#" + "parent-sidebar-check-" + sectionId).addClass(
              "fa-check-circle"
            );
            $("#" + "parent-sidebar-check-" + sectionId).addClass("icon-green");
          } else {
            $("#" + "parent-sidebar-check-" + sectionId).removeClass(
              "fa-check-circle"
            );
            $("#" + "parent-sidebar-check-" + sectionId).removeClass(
              "icon-green"
            );
            $("#" + "parent-sidebar-check-" + sectionId).addClass(
              "fa-exclamation-circle"
            );
            $("#" + "parent-sidebar-check-" + sectionId).addClass("icon-red");
          }
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    });
  }

  function sectionProgressMarker(section_progress_url, sectionId) {
    //Gets the progress for a specific section and sets the desired section's progress

    $.ajax({
      type: "GET",
      url: section_progress_url,
      success: function (response) {
        if (response.progress)
          $("#" + sectionId + "-fa-circle").attr(
            "style",
            "color: green !important"
          );
        else
          $("#" + sectionId + "-fa-circle").attr(
            "style",
            "color: grey !important"
          );
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  }

  $('input[type="radio"]').on("change", function () {
    // Events to occure when a radio input changes
    var questionId = $(this).data("question-id");
    var radioLabel = $(this).data("radio-label");
    var sectionId = $(this).closest("[data-section-id]").data("section-id");
    var documentId = $(".page-wrapper").data("document-id");

    var postData = {
      section_id: sectionId,
      question_id: questionId,
      user_document_id: documentId,
      new_answer_text: radioLabel,
    };

    // Saving to database
    $.ajax({
      type: "POST",
      url: "/create_or_update_answer",
      data: postData,
      success: function (response) {
        $("#" + questionId + ".fa-check-circle").attr(
          "style",
          "color: green !important"
        );
        var section_progress_url =
          "/get_section_progress/" + sectionId + "/" + documentId;
        sectionProgressMarker(section_progress_url, sectionId);
        setSidebarProgressMarkers();
        setSectionProgressElements();
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });

    display_and_hide_radio(questionId, radioLabel);
  });

  function display_and_hide_radio(questionId, radioLabel) {
    cascaded_questions_hide(questionId);
    cascaded_questions_display(questionId, radioLabel);
  }

  function cascaded_questions_display(questionId, radioLabel) {
    var questions = $(".child_question")
      .filter(
        '[data-parent-question="' +
          questionId +
          '"][data-parent-option="' +
          radioLabel +
          '"]'
      )
      .attr("hidden", false);
    questions.each(function (index, question) {
      var checkedInputLabel = $(question).find("input:checked");
      cascaded_questions_display(
        $(question).data("question-id"),
        $(checkedInputLabel).data("radio-label")
      );
    });
  }

  function cascaded_questions_hide(questionId) {
    var questions = $(".child_question")
      .filter('[data-parent-question="' + questionId + '"]')
      .attr("hidden", true);
    questions.each(function (index, question) {
      cascaded_questions_hide($(question).data("question-id"));
    });
  }

  // $('input[type="text"]').on("blur", function () {
  // Events to occure when a text input changes
  $(".atextarea").on("blur", function () {
    var questionId = $(this).closest("[data-question-id]").data("question-id");
    var documentId = $(".page-wrapper").data("document-id");
    var sectionId = $(this).closest("[data-section-id]").data("section-id");
    var answerText = $(this).val();
    var postData = {
      section_id: sectionId,
      question_id: questionId,
      user_document_id: documentId,
      new_answer_text: answerText,
    };

    if (/^\s*$/.test(answerText)) {
      $("#" + questionId + ".fa-check-circle").attr(
        "style",
        "color: red !important"
      );

      // Delete from database

      $.ajax({
        type: "POST",
        url: "/delete_empty_answer",
        data: postData,
        success: function (response) {
          if (answerText == "")
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: red !important"
            );
          else {
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: green !important"
            );
          }

          var section_progress_url =
            "/get_section_progress/" + sectionId + "/" + documentId;
          sectionProgressMarker(section_progress_url, sectionId);
          setSidebarProgressMarkers();
          setSectionProgressElements();
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
      return;
    }

    // Saving to database
    $.ajax({
      type: "POST",
      url: "/create_or_update_answer",
      data: postData,
      success: function (response) {
        if (answerText == "")
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: red !important"
          );
        else {
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: green !important"
          );
        }

        var section_progress_url =
          "/get_section_progress/" + sectionId + "/" + documentId;
        sectionProgressMarker(section_progress_url, sectionId);
        setSidebarProgressMarkers();
        setSectionProgressElements();
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  });

  $('input[type="date"]').on("blur", function () {
    var questionId = $(this).closest("[data-question-id]").data("question-id");
    var documentId = $(".page-wrapper").data("document-id");
    var sectionId = $(this).closest("[data-section-id]").data("section-id");
    var answerText = $(this).val();
    var postData = {
      section_id: sectionId,
      question_id: questionId,
      user_document_id: documentId,
      new_answer_text: answerText,
    };

    if (answerText.trim() == "") {
      // Delete from database
      $.ajax({
        type: "POST",
        url: "/delete_empty_answer",
        data: postData,
        success: function (response) {
          if (answerText == "")
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: red !important"
            );
          else {
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: green !important"
            );
          }

          var section_progress_url =
            "/get_section_progress/" + sectionId + "/" + documentId;
          sectionProgressMarker(section_progress_url, sectionId);
          setSidebarProgressMarkers();
          setSectionProgressElements();
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    } else {
      // Saving to database
      $.ajax({
        type: "POST",
        url: "/create_or_update_answer",
        data: postData,
        success: function (response) {
          if (answerText == "")
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: red !important"
            );
          else {
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: green !important"
            );
          }

          var section_progress_url =
            "/get_section_progress/" + sectionId + "/" + documentId;
          sectionProgressMarker(section_progress_url, sectionId);
          setSidebarProgressMarkers();
          setSectionProgressElements();
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    }
  });

  $('input[type="number"]').on("blur", function () {
    var questionId = $(this).closest("[data-question-id]").data("question-id");
    var documentId = $(".page-wrapper").data("document-id");
    var sectionId = $(this).closest("[data-section-id]").data("section-id");
    var answerText = $(this).val();
    var postData = {
      section_id: sectionId,
      question_id: questionId,
      user_document_id: documentId,
      new_answer_text: answerText,
    };

    if (answerText.trim() == "") {
      // Delete from database
      $.ajax({
        type: "POST",
        url: "/delete_empty_answer",
        data: postData,
        success: function (response) {
          if (answerText == "")
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: red !important"
            );
          else {
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: green !important"
            );
          }

          var section_progress_url =
            "/get_section_progress/" + sectionId + "/" + documentId;
          sectionProgressMarker(section_progress_url, sectionId);
          setSidebarProgressMarkers();
          setSectionProgressElements();
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    } else {
      // Saving to database
      $.ajax({
        type: "POST",
        url: "/create_or_update_answer",
        data: postData,
        success: function (response) {
          if (answerText == "")
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: red !important"
            );
          else {
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: green !important"
            );
          }

          var section_progress_url =
            "/get_section_progress/" + sectionId + "/" + documentId;
          sectionProgressMarker(section_progress_url, sectionId);
          setSidebarProgressMarkers();
          setSectionProgressElements();
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    }
  });

  $('input[type="file"]').on("change", function () {
    // Events to occur when a file input changes
    var questionId = $(this).closest("[data-question-id]").data("question-id");
    var documentId = $(".page-wrapper").data("document-id");
    var sectionId = $(this).closest("[data-section-id]").data("section-id");
    var answerFile = $(this).prop("files")[0]; // Get the selected file
    var postData = new FormData(); // Create a FormData object to send file data

    // Append data to FormData object
    postData.append("section_id", sectionId);
    postData.append("question_id", questionId);
    postData.append("user_document_id", documentId);
    postData.append("new_answer_text", answerFile);

    // Saving to database
    $.ajax({
      type: "POST",
      url: "/create_or_update_image_answer_view",
      data: postData,
      processData: false, // Prevent jQuery from processing data
      contentType: false, // Prevent jQuery from setting contentType
      success: function (response) {
        if (!response.error) {
          $("#" + questionId + ".fa-check-circle").css(
            "color",
            "green !important"
          );
        } else {
          $("#" + questionId + ".fa-check-circle").css(
            "color",
            "red !important"
          );
        }
        location.reload();
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  });

  // Trigger video loading when video icon is clicked
  $(document).on("click", ".fa-video", function () {
    var question_id = $(this).data("bs-target").replace("#video_modal_", "");
    loadVideo(question_id);
  });

  // Function to resize the textarea based on its content
  function defaultResizeTextarea(textarea) {
    textarea.css("height", "auto"); // Reset the height
    textarea.css("height", textarea.prop("scrollHeight") + "px"); // Set the height to the scroll height
  }

  // Expand the height of all textareas with the class .atextarea on page load
  $(".atextarea").each(function () {
    defaultResizeTextarea($(this));
  });

  // Resize the textarea as the user types
  $(document).on("input", ".atextarea", function () {
    defaultResizeTextarea($(this));
  });
});

  // Function to handle fetching and embedding the video
  function loadVideo(question_id) {
    var videoContentId = "#video_content_" + question_id;
    var modalElement = "#video_modal_" + question_id;

    // Fetch video embed code from API
    $.ajax({
      type: "GET",
      url: "/get_question_video",
      data: {
        question_id: question_id,
      },
      success: function (response) {
        $(videoContentId).html(response.video_embed_code);
      },
      error: function (error) {
        console.error("Error fetching video:", error);
        $(videoContentId).html("<p>Error loading video.</p>");
      },
    });

    $(modalElement).on("shown.bs.modal", function () {
      var iframe = $(videoContentId).find("iframe");
      if (iframe.length > 0) {
        // Append autoplay to the video URL if not already present
        var src = iframe.attr("src");
        if (!src.includes("autoplay=1")) {
          var separator = src.includes("?") ? "&" : "?";
          iframe.attr("src", src + separator + "autoplay=1");
        }

        // Programmatically start the video by accessing the iframe's content
        var iframeWindow = iframe[0].contentWindow;
        iframeWindow.postMessage(
          '{"event":"command","func":"playVideo","args":""}',
          "*"
        );
      }
    });

    // Stop video when modal closes
    $(modalElement).on("hidden.bs.modal", function () {
      var iframe = $(videoContentId).find("iframe");
      if (iframe.length > 0) {
        var src = iframe.attr("src").split("?")[0]; // Remove query parameters to stop video
        iframe.attr("src", src);

        // Programmatically stop the video
        var iframeWindow = iframe[0].contentWindow;
        iframeWindow.postMessage(
          '{"event":"command","func":"pauseVideo","args":""}',
          "*"
        );
      }
    });
  }


function buttonClick(button){
  var question_id = $(button).data("question-id");
  var textarea_id = "#text_area_" + question_id;
  var textarea = $(textarea_id);
  textarea.val("NOT APPLICABLE");
  textarea.trigger("blur");
}

function aiButtonClick(button){
  var question_id = $(button).data("question-id");
  var textarea_id = "#text_area_" + question_id;
  var promptarea_id = "#prompt_" + question_id;
  var promptValue = $(promptarea_id).val();
  var modalElement = "#generative_text_modal_" + question_id;
  var textarea = $(textarea_id);
  // Show spinner
  $(button).find(".spinner-border").removeClass("d-none");
  $.ajax({
    type: "GET",
    url: "/get_ai_answer",
    data: {
      question_id: question_id,
      prompt_value: promptValue,
    },
    success: function (response) {
      textarea.val(response.answer);
      resizeTextarea(textarea);
      textarea.trigger("blur");
    },
    error: function (error) {
      console.error("Error:", error);
    },
    complete: function () {
      // Hide spinner when AJAX request completes
      $(button).find(".spinner-border").addClass("d-none");
      $(modalElement).modal("hide");
    },
  });
}

function resizeTextarea(textarea) {
  textarea.css("height", "auto");
  textarea.css("height", textarea.prop("scrollHeight") + "px");
}

function addInput(button) {
  var questionId = $(button).data("question-id");
  var documentId = $(".page-wrapper").data("document-id");
  var sectionId = $(button).closest("[data-section-id]").data("section-id");
  let new_input_id = "multiple-" + questionId;
  let inputs = document.querySelectorAll('input[id^="' + new_input_id + '"].form-control');
  let answerText = "";
  inputs.forEach((input, index) => {
    if (input.value != ''){
      answerText += input.value;
      if (index < inputs.length - 1) {
        answerText += "|";
      }
    }
  });


  var postData = {
    section_id: sectionId,
    question_id: questionId,
    user_document_id: documentId,
    new_answer_text: answerText,
  };

  if (answerText.trim() == "") {

      // Delete from database
      $.ajax({
        type: "POST",
        url: "/delete_empty_answer",
        data: postData,
        success: function (response) {
          if (answerText == "")
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: red !important"
            );
          else {
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: green !important"
            );
          }

          var section_progress_url =
            "/get_section_progress/" + sectionId + "/" + documentId;
          sectionProgressMarker(section_progress_url, sectionId);
          setSidebarProgressMarkers();
          setSectionProgressElements();
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });

  } else {

    $.ajax({
      type: "POST",
      url: "/create_or_update_answer",
      data: postData,
      success: function (response) {
        if (answerText == "")
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: red !important"
          );
        else {
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: green !important"
          );
        }

        var section_progress_url =
          "/get_section_progress/" + sectionId + "/" + documentId;
        sectionProgressMarker(section_progress_url, sectionId);
        setSidebarProgressMarkers();
        setSectionProgressElements();
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
    
    let container = button.parentNode.parentNode;
    let newInputRow = document.createElement("div");
    newInputRow.classList.add("input-row");
    newInputRow.innerHTML = `
          <input type="text" id="${new_input_id}" style="margin-left:20px;" class="dynamic-input form-control mt-2" onblur='saveInputData(this)'>
          <button class='btn btn-sm btn-danger mt-2' style="margin-left: 20px;" onclick="removeInput(this)" data-question-id=${questionId} >-</button>
      `;

    container.appendChild(newInputRow);
  }
}

function removeInput(button) {
  var questionId = $(button).data("question-id");
  var documentId = $(".page-wrapper").data("document-id");
  var sectionId = $(button).closest("[data-section-id]").data("section-id");
  let new_input_id = "multiple-" + questionId;
  button.parentNode.remove();

  let inputs = document.querySelectorAll('input[id^="' + new_input_id + '"]');
  let answerText = "";
  inputs.forEach((input, index) => {
    if (input.value != ''){
      answerText += input.value;
      if (index < inputs.length - 1) {
        answerText += "|";
      }
    }
  });

  var postData = {
    section_id: sectionId,
    question_id: questionId,
    user_document_id: documentId,
    new_answer_text: answerText,
  };

  if (answerText.trim() == "") {

    // Delete from database
    $.ajax({
      type: "POST",
      url: "/delete_empty_answer",
      data: postData,
      success: function (response) {
        if (answerText == "")
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: red !important"
          );
        else {
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: green !important"
          );
        }

        var section_progress_url =
          "/get_section_progress/" + sectionId + "/" + documentId;
        sectionProgressMarker(section_progress_url, sectionId);
        setSidebarProgressMarkers();
        setSectionProgressElements();
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });

} else {

    $.ajax({
      type: "POST",
      url: "/create_or_update_answer",
      data: postData,
      success: function (response) {
        if (answerText == "")
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: red !important"
          );
        else {
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: green !important"
          );
        }

        var section_progress_url =
          "/get_section_progress/" + sectionId + "/" + documentId;
        sectionProgressMarker(section_progress_url, sectionId);
        setSidebarProgressMarkers();
        setSectionProgressElements();
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  }
}

function sectionProgressMarker(section_progress_url, sectionId) {
  //Gets the progress for a specific section and sets the desired section's progress

  $.ajax({
    type: "GET",
    url: section_progress_url,
    success: function (response) {
      if (response.progress)
        $("#" + sectionId + "-fa-circle").attr(
          "style",
          "color: green !important"
        );
      else
        $("#" + sectionId + "-fa-circle").attr(
          "style",
          "color: grey !important"
        );
    },
    error: function (error) {
      console.error("Error:", error);
    },
  });
}

function setSidebarProgressMarkers() {
  $(".s_check").each(function () {
    var documentId = $(".page-wrapper").data("document-id");
    var sectionId = $(this).data("section-id");
    var section_progress_url =
      "/get_section_progress/" + sectionId + "/" + documentId;
    $.ajax({
      type: "GET",
      url: section_progress_url,
      success: function (response) {
        if (response.progress) {
          $("#" + "sidebar-check-" + sectionId).attr("hidden", false);
        } else {
          $("#" + "sidebar-check-" + sectionId).attr("hidden", true);
        }
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  });
  $(".ps_section").each(function () {
    var documentId = $(".page-wrapper").data("document-id");
    var sectionId = $(this).data("parent-section-id");
    var section_progress_url =
      "/get_parent_section_progress/" + sectionId + "/" + documentId;
    $.ajax({
      type: "GET",
      url: section_progress_url,
      success: function (response) {
        if (response.progress) {
          $("#" + "parent-sidebar-check-" + sectionId).removeClass(
            "fa-exclamation-circle"
          );
          $("#" + "parent-sidebar-check-" + sectionId).removeClass(
            "icon-red"
          );
          $("#" + "parent-sidebar-check-" + sectionId).addClass(
            "fa-check-circle"
          );
          $("#" + "parent-sidebar-check-" + sectionId).addClass(
            "icon-green"
          );
        } else {
          $("#" + "parent-sidebar-check-" + sectionId).removeClass(
            "fa-check-circle"
          );
          $("#" + "parent-sidebar-check-" + sectionId).removeClass(
            "icon-green"
          );
          $("#" + "parent-sidebar-check-" + sectionId).addClass(
            "fa-exclamation-circle"
          );
          $("#" + "parent-sidebar-check-" + sectionId).addClass(
            "icon-red"
          );
        }
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  });
}

function setSectionProgressElements() {
  var label = document.querySelector(".progress_label");
  var subsectionId = label.id;
  if (subsectionId) {
    var documentId = $(".page-wrapper").data("document-id");
    var elements_url =
      "/get_subsection_progress/" + subsectionId + "/" + documentId;
    $.ajax({
      type: "GET",
      url: elements_url,
      success: function (response) {
        document.getElementById("answered_questions").innerText =
          response.answered_question;
        document.getElementById("total_questions").innerText =
          response.total_questions;
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  }
}

function saveInputData(input){
  var questionId = $(input).closest("[data-question-id]").data("question-id");
  var documentId = $(".page-wrapper").data("document-id");
  var sectionId = $(input).closest("[data-section-id]").data("section-id");
  let new_input_id = "multiple-" + questionId;
  let inputs = document.querySelectorAll('input[id^="' + new_input_id + '"]');
  let answerText = "";
  inputs.forEach((input, index) => {
    if (input.value != ''){
      answerText += input.value;
      if (index < inputs.length - 1) {
        answerText += "|";
      }
    }
  });

  var postData = {
    section_id: sectionId,
    question_id: questionId,
    user_document_id: documentId,
    new_answer_text: answerText,
  };

  if (answerText.trim() == "") {

      // Delete from database
      $.ajax({
        type: "POST",
        url: "/delete_empty_answer",
        data: postData,
        success: function (response) {
          if (answerText == "")
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: red !important"
            );
          else {
            $("#" + questionId + ".fa-check-circle").attr(
              "style",
              "color: green !important"
            );
          }

          var section_progress_url =
            "/get_section_progress/" + sectionId + "/" + documentId;
          sectionProgressMarker(section_progress_url, sectionId);
          setSidebarProgressMarkers();
          setSectionProgressElements();
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });

  } else {

    $.ajax({
      type: "POST",
      url: "/create_or_update_answer",
      data: postData,
      success: function (response) {
        if (answerText == "")
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: red !important"
          );
        else {
          $("#" + questionId + ".fa-check-circle").attr(
            "style",
            "color: green !important"
          );
        }

        var section_progress_url =
          "/get_section_progress/" + sectionId + "/" + documentId;
        sectionProgressMarker(section_progress_url, sectionId);
        setSidebarProgressMarkers();
        setSectionProgressElements();
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  }
}

// Admin Dashboard Management
class AdminDashboardManager {
    constructor() {
        this.initializeAdminDashboard();
        this.setupAdminEventListeners();
    }

    initializeAdminDashboard() {
        this.updateAdminMetrics();
        this.initializeAdminUI();
    }

    updateAdminMetrics() {
        this.fetchAdminStatistics();
        this.updateAdminProgressIndicators();
        this.refreshAdminNotifications();
    }

    async fetchAdminStatistics() {
        try {
            const response = await fetch('/admin/api/statistics');
            const data = await response.json();
            this.updateAdminMetricDisplays(data);
        } catch (error) {
            console.error('Admin Error:', error);
            this.handleAdminError(error);
        }
    }

    handleAdminTemplateUpdate(templateId, updateData) {
        return fetch(`/admin/api/templates/${templateId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(updateData)
        })
        .then(this.handleAdminResponse)
        .catch(this.handleAdminError);
    }

    setupAdminEventListeners() {
        document.querySelectorAll('.admin-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleAdminAction(e));
        });
    }
}

// Initialize admin functionality
const adminManager = new AdminDashboardManager();
