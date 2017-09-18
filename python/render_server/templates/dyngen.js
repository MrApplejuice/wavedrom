"use strict"

define(["jquery"], function($) {
	return {
		dynamically_update_generated_section:
			function (code_area, scale_area, image_type_area, content_area) {
				code_area = $(code_area);
				scale_area = $(scale_area);
				image_type_area = $(image_type_area);
				content_area = $(content_area);
				
				var current_timeout = null;
				var request_running = false;
				var queue_update = false;
				
				function change_update_timer() {
					const UPDATE_TIMEOUT = 500;
					
					if (!request_running) {
						queue_update = false;
						if (current_timeout !== null) {
							window.clearTimeout(current_timeout);
							current_timeout = null;
						}
						
						current_timeout = window.setTimeout(do_update, UPDATE_TIMEOUT);
					} else {
						queue_update = true;
					}
				}
				
				function do_update() {
					var code = code_area.val();
					
					$.ajax(
						"/rest/generate_link",
						{
							method: "POST",
							data: {
								code: code,
								scale: scale_area.val(),
								type: image_type_area.val()
							}
						}).done(function(data) {
							content_area.html(
								'<input class="link" value="' + data + '" type="text" />'
								+ '<img src="' + data + '" />'
							);
							
							content_area.find("input.link").on("mouseup mousedown", function sel_all(el) { 
								el.currentTarget.select();
							});
						}).fail(function(request) {
							var data = $.parseJSON(request.responseText);
							content_area.html(
								'<p class="link-error title">' + data.title + ':</p>'
								+ '<p class="link-error text">' + data.description + '</p>'
							);
						}).always(function() {
							request_running = false;
							current_timeout = null;
							if (queue_update) {
								change_update_timer();
							}
						});
					
				}
				
				code_area.on("change", change_update_timer);
				code_area.on("keydown", change_update_timer);
				scale_area.on("change", change_update_timer);
				scale_area.on("keydown", change_update_timer);
				image_type_area.on("change", change_update_timer);
				image_type_area.on("keydown", change_update_timer);
				
				return do_update;
			}
	};
});
