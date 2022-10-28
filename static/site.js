$(document).ready(function(){

  function save_form() {
    // save settings to localstorage
    localStorage.hostname = $("#hostname").val();
    localStorage.username = $("#username").val();
    localStorage.password = $("#password").val();
    localStorage.local_path = $("#local_path").val();
    localStorage.remote_path = $("#remote_path").val();
  };

  function load_form() {
    // load settings from localstorage
    if(localStorage.hostname) {
      $("#hostname").val(localStorage.hostname);
    }
    $("#username").val(localStorage.username);
    $("#password").val(localStorage.password);
    $("#local_path").val(localStorage.local_path);
    $("#remote_path").val(localStorage.remote_path);
    highlight_button(localStorage.highlighted_button);
  };

  function highlight_button(button_id) {
    // highlight given button (and unhighlight all others)
    $("button").css({"border-bottom": "3px solid black",
                     "filter": "",
                    });
    $(button_id).css({"border-bottom": "3px solid black",
                      "filter": "brightness(125%)",
                     });
    localStorage.highlighted_button = button_id;
  }

  // buttons click callbacks
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
        local_path: $("#local_path").val(),
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

  $("#term_remote_shell").click(function() {
    save_form();
    highlight_button("#term_remote_shell")

    $.ajax({
      method: "POST",
      url: "/api/remote_shell",
      data: {
        hostname: $("#hostname").val(),
        username: $("#username").val(),
        password: $("#password").val(),
        remote_path: $("#remote_path").val(),
      }
    });
  });

  // save form on every keyup
  $(document).keyup(function(e) {
    save_form();
  });

  load_form();
});
