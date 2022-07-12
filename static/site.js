function save_form() {
  localStorage.hostname = $("#hostname").val();
  localStorage.username = $("#username").val();
  localStorage.password = $("#password").val();
  localStorage.local_path = $("#local_path").val();
  localStorage.remote_path = $("#remote_path").val();
};

function load_form() {
  $("#hostname").val(localStorage.hostname);
  $("#username").val(localStorage.username);
  $("#password").val(localStorage.password);
  $("#local_path").val(localStorage.local_path);
  $("#remote_path").val(localStorage.remote_path);
  highlight_button(localStorage.highlighted_button);
};

function highlight_button(button_id) {
  $("button").css("border-bottom", "");
  $(button_id).css("border-bottom", "3px solid black");
  localStorage.highlighted_button = button_id;
}

$("#term_watch_queue").click(function() {
  save_form();
  highlight_button("#term_watch_queue")

  $.ajax({
    method: "POST",
    url: "/api/watch_queue",
    data: {
      hostname: $("#hostname").val(),
      username: $("#username").val(),
      password: $("#password").val(),
    }
  });
});

$("#term_run").click(function() {
  save_form();
  highlight_button("#term_run")

  $.ajax({
    method: "POST",
    url: "/api/run",
    data: {
      hostname: $("#hostname").val(),
      username: $("#username").val(),
      password: $("#password").val(),
      remote_path: $("#remote_path").val(),
    }
  });
});

$("#term_rsync_up").click(function() {
  save_form();
  highlight_button("#term_rsync_up")

  $.ajax({
    method: "POST",
    url: "/api/rsync_up",
    data: {
      hostname: $("#hostname").val(),
      username: $("#username").val(),
      password: $("#password").val(),
      local_path: $("#local_path").val(),
      remote_path: $("#remote_path").val(),
    }
  });
});

$("#term_rsync_down").click(function() {
  save_form();
  highlight_button("#term_rsync_down")

  $.ajax({
    method: "POST",
    url: "/api/rsync_down",
    data: {
      hostname: $("#hostname").val(),
      username: $("#username").val(),
      password: $("#password").val(),
      local_path: $("#local_path").val(),
      remote_path: $("#remote_path").val(),
    }
  });
});

$("#filebrowser").click(function() {
  save_form();
  highlight_button("#filebrowser")

  $.ajax({
    method: "POST",
    url: "/api/filebrowser",
    data: {
      local_path: $("#local_path").val(),
    }
  });
});

$("#cancel_all_jobs").click(function() {
  save_form();
  highlight_button("#cancel_all_jobs")

  $.ajax({
    method: "POST",
    url: "/api/cancel_all_jobs",
    data: {
      hostname: $("#hostname").val(),
      username: $("#username").val(),
      password: $("#password").val(),
    }
  });
});

load_form();
