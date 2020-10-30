$(function() {
    /*Show corresponding network list as soon as organization is choosen in dropdown + reset child fields*/
    $('#organizations_select').bind('change', function() {
          $('.network-select').attr("hidden", true);
          $('.network-select .networks').val("0");
          $('.network-select .networks').attr("required", true);
          $('.camera-checkboxes').attr("hidden", true);
          var selectid = $( "#organizations_select option:selected" ).val();
          $('#' + selectid).attr("hidden",false);       
      });                            
  });  