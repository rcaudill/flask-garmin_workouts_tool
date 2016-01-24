    function onFileSelected(event) {
    var selectedFile = event.target.files[0];
    var reader = new FileReader();
    var result = document.getElementById("workout_json");
    reader.onload = function(event) {
      result.innerHTML = event.target.result;
      result.rows = "20";
      result.cols = "80";
    };
    reader.readAsText(selectedFile);

    show(document.getElementById('edit_field'));
    }
    function hide (elements) {
      if (elements!=null){
      elements = elements.length ? elements : [elements];
      for (var index = 0; index < elements.length; index++) {
        elements[index].style.display = 'none';
      }
      }
    }
    function show (elements, specifiedDisplay) {
      if (elements!=null){
          elements = elements.length ? elements : [elements];
          for (var index = 0; index < elements.length; index++) {
            elements[index].style.display = specifiedDisplay || 'block';
          }
      }
    }

    window.onload = hide(document.getElementById('edit_field'));
    window.onload = hide(document.getElementById('workout-list-json-field'));
    window.onload = hide(document.getElementById('schedule-json-field'));

    var idshowworkoutlistjson = document.getElementById('show-workout-list-json');
    if (idshowworkoutlistjson != null) {
        idshowworkoutlistjson.addEventListener('click', function () {
            show(document.getElementById('workout-list-json-field'));
        });
    }

    var idshowschedulejson = document.getElementById('show-schedule-json');
    if (idshowschedulejson != null) {
        idshowschedulejson.addEventListener('click', function () {
            show(document.getElementById('schedule-json-field'));
        });
    }