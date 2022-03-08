$(document).ready(function(){
	var arrow = $('.chat-head img');
	var textarea = $('.chat-text textarea');
	var start_button = $('.dialog-start_button');
	var additional_data = {};
	var request_counter = 0;
	var base_url = ""
	
	var chat_head_height = $(".chat-head").height();
	var chat_text_height = $(".chat-text").height();
    var chat_box_height = $(".chat-box").height();
	//console.log(chat_head_height);
	//console.log(chat_box_height);
	//console.log(chat_text_height);
	
	var chat_body_height = chat_box_height - chat_head_height - chat_text_height;
	$(".chat-body").height(chat_body_height); 
	//console.log($(".chat-body").height());
	
	$(window).resize(function() {
		chat_head_height = $(".chat-head").height();
		chat_text_height = $(".chat-text").height();
		chat_box_height = $(".chat-box").height();
			
	    chat_body_height = chat_box_height - chat_head_height - chat_text_height;
		$(".chat-body").height(chat_body_height); 
	});
	
	
	
	$.ajax({
				url: base_url + "/get_history/",
				data: {},
				type: "post",
				success: restoreDialog
			})
			
			
	function restoreDialog(data) {		
		if (data.length > 0) {
			console.log(data);
			$(".msg-insert").empty();					
			$('.msg-insert').append("<div class='msg-receive'>Hello! This is a reference system about Heydar Aliyev. Do you have any questions? </div>");
			for (var item_n in data) {
				if (typeof data[item_n]["type"] != "undefined") {
					if (data[item_n]["type"] == "question") {
						$('.msg-insert').append("<div class='msg-send'>"+data[item_n]["question"]+"</div>");
					} else {
						distlayResponse(data[item_n]);
					}
				}				
			}
			stopDialogButton();
            $(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
			
			$(".chat-text_input").removeAttr("disabled");
			$(".chat-text_input").attr("placeholder", "Type your question here and press 'Enter'...");
		} else {
			console.log("session is new");
			$(".chat-text_input").attr("placeholder", "Click the button above to start the dialog.");
		}		
	}
	

	arrow.on('click', function(){
		var src = arrow.attr('src');
		
		$('.chat-body').slideToggle('slow');		
		
		if(src == 'https://maxcdn.icons8.com/windows10/PNG/16/Arrows/angle_down-16.png'){
			arrow.attr('src', 'https://maxcdn.icons8.com/windows10/PNG/16/Arrows/angle_up-16.png');
			
			$('.chat-box').animate({height:"45px"}, 'slow');
			$('.chat-text').animate({height:"1px"}, 'fast');
			
		}
		else{
			arrow.attr('src', 'https://maxcdn.icons8.com/windows10/PNG/16/Arrows/angle_down-16.png');
			$('.chat-box').animate({height:"90%"}, 'slow');
			$('.chat-text').animate({height:"65px"}, 'fast');
		}
	});
	
	

	textarea.keypress(function(event) {

		var $this = $(this);	

		if(event.keyCode == 13){
			$(".dialog-button").prop('disabled', true);
			$(".stop_dialog-button").parent().remove();
			$(".stop_dialog-button-positive").parent().remove();
			var msg = $this.val();
			$this.val('');
			var current_data = {"question": msg}
			$('.msg-insert').append("<div class='msg-send'>"+msg+"</div>");
			request_counter = 0;
			$(".chat-text_input").empty();
			$(".chat-text_input").attr("placeholder", "Waiting for an answer...");
			$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
			$.ajax({
				url: base_url + "/aliyev/process_question/",
				data: current_data,
				type: "post",
				success: requestAnswer
			})
			
			
			
			/*
			
			$('.msg-insert').append("<div class='msg-receive'>Send a new message</div>");
			$('.msg-insert').append("<div class='msg-receive'><button>qwertyqqqqqqqqqqqqqqqqqqqqqqqq</button></div>");
			*/
			}
	});
	
	$(".msg-insert").on('click', ".dialog-start_button", function(e){
		e.preventDefault();
		$(".chat-text_input").attr("placeholder", "Connecting to server ... Please wait.");
		$(".dialog-button").prop('disabled', true);
		$(".start-dialog_replic").remove();
		$.ajax({
			url: base_url + "/aliyev/",
			data: {},
			type: "post",
			success: startNewDialog,
				complete: function(jqXHR, status) {
					$(".dialog-button").removeAttr("disabled");
					$(".chat-text_input").attr("placeholder", "Type your question here and press 'Enter'...");
					$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
				}
		})
		
	});
	
	$(".msg-insert").on('click', ".show-additional_button", function(e){
		e.preventDefault();		
		
		new_msg = additional_data[$(this).attr("name")];
		if (new_msg != "undefined" && new_msg != "") {
			$(this).parent().append(new_msg);
		}
		$(this).remove();		
	});	
	
	function startNewDialog(data) {
		$(".chat-text_input").removeAttr("disabled");		
        $('.msg-insert').append("<div class='msg-receive'>" + data["greeting_phrase"] +"</div>");
		stopDialogButton();
		
	}
	
	function requestAnswer(data) {
		/* console.log(data); */
		$(".chat-text_input").val("");
		request_counter += 1;
		var anwerExist = false;
		
		if ((request_counter <= 3000) &&(typeof data["tech_response"] != "undefined") && (data["tech_response"] == "is_standard")) {
			for (var key in data["primary_answers"]) {
				var answer_phrase = formAnswerPhrase(data["primary_answers"][key]);							
				$('.msg-insert').append("<div class='msg-receive'>" + answer_phrase +"</div>");
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Type your question here and press 'Enter'...");
				$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
				stopDialogButton();
			}
		} else {
			
			$.ajax({
				url: base_url + "/get_answer/",
				data: {"sparql_converter_result": data["sparql_converter_result"],
						"is_too_long": data["is_too_long"], "ontology": "aliyev"},
				type: "post",
				success: function (data_2) {
						/*console.log((typeof data_2["tech_response"] !== "undefined") && (data_2["tech_response"] == "in_process"));*/
						if ((request_counter <= 3000) &&(typeof data_2["tech_response"] != "undefined") && (data_2["tech_response"] == "in_process")) {
							anwerExist = false;
							setTimeout(requestAnswer (data), 1000);
						} else {
							anwerExist = true;
							$(".dialog-button").prop('disabled', false);
							console.log(data_2);
							distlayResponse(data_2);
							stopDialogButton();
							$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
							$(".chat-text_input").attr("placeholder", "Type your question here and press 'Enter'...");
						}
					}
			})
		}
		
	}
			
			
	function formAnswerPhrase(dataItem) {
		var answer_phrase = "";
		
		if ((typeof dataItem["comment"] != "undefined") && (dataItem["name"] != "")) {
			answer_phrase += "<strong><i>" +  dataItem["comment"] + "</i></strong><br />"	;							
		}
		if ((typeof dataItem["name"] != "undefined") && (dataItem["name"] != "")) {
			answer_phrase += "<b>" +  dataItem["name"] + "</b><br />"	;							
		}							
		
		if (dataItem["semantic_type"] == "predicate_definition") {
			if (typeof dataItem["entities_for_query"] !== "undefined") {
				if (typeof dataItem["entities_for_query"]["inputEntity"] != "undefined") {
					answer_phrase += "<strong>" + dataItem["entities_for_query"]["inputEntity"] + "</strong>";
				}
			}
		} else if (dataItem["semantic_type"] == "super_class") {
			if (typeof dataItem["entities_for_query"] != "undefined") {
				if (typeof dataItem["entities_for_query"]["inputEntity"] != "undefined") {
					answer_phrase += "<strong>" + dataItem["entities_for_query"]["inputEntity"] + "</strong> relates to <i><b>\"";
				}
			}
			
		} else if (dataItem["semantic_type"] == "predicate_query") {
			if (typeof dataItem["entities_for_query"] != "undefined") {
				if (typeof dataItem["entities_for_query"]["inputEntity"] != "undefined") {
					answer_phrase += "<strong>" + dataItem["entities_for_query"]["inputEntity"] + "</strong> ";
				}
			}
			
		}
		
		if ((typeof dataItem["content"] != "undefined") && (dataItem["content"] != "")) {
			answer_phrase += "<br />" + dataItem["content"];
			if (dataItem["semantic_type"] == "super_class" && dataItem["entities_for_query"] != "undefined") {
				answer_phrase += "\"<b><i>";
			}
		}
		return answer_phrase;		
	}
	
	
	
	function stopDialogButton() {
		$(".stop_dialog-button").parent().remove();
		$(".stop_dialog-button-positive").parent().remove();
		$('.msg-insert').append("<div class='msg-receive'><button class='stop_dialog-button dialog-button'>Finish the dialogue</button></div>");

		
	}
	
	
	$(".msg-insert").on('click', ".stop_dialog-button", function(e){
		e.preventDefault();
		$(this).parent().append("Did you get answers to your questions? <br /><button class='stop_dialog-button-positive dialog-button'><b>Yes</b></button><button class='stop_dialog-button-negative dialog-button'><b>No</b></button>");
		$(this).remove();
		$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
		
	});
	
	
	$(".msg-insert").on('click', ".stop_dialog-button-positive", function(e){
		e.preventDefault();
		
		$(this).parent().remove();
		$(".msg-insert").empty();
		$(".dialog-button").prop('disabled', true);
		$(".chat-text_input").prop('disabled', true);
		$(".chat-text_input").attr("placeholder", "Connecting to server ... Please wait.");
		
		$(".start-dialog_replic").remove();
		$.ajax({
			url: base_url + "/ask_unsubscribe/",
			data: {"result": "True"},
			type: "post",
			success: function (data) {
				
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'> Do you want to start a conversation?  </div>");
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'><button class='dialog-button dialog-start_button'>Start a new dialogue </button></div>");
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Click the button to start the dialog");
			},
			complete: function(jqXHR, status) {
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Click the button to start the dialog");
			}
		})	
		
	});
		
		
	$(".msg-insert").on('click', ".stop_dialog-button-negative", function(e){
		e.preventDefault();
		$(this).parent().remove();
		$(".msg-insert").empty();
		$(".dialog-button").prop('disabled', true);
		$(".chat-text_input").prop('disabled', true);		
		$(".start-dialog_replic").remove();
		$(".chat-text_input").attr("placeholder", "Connecting to server ... Please wait.");
		$.ajax({
			url: base_url + "/ask_unsubscribe/",
			data: {"result": "False"},
			type: "post",
			success: function (data) {
				
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'> Are you to start a conversation? </div>");
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'><button class='dialog-button dialog-start_button'>Start a new dialogue</button></div>");
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Click the button to start the dialog");
			},
			complete: function(jqXHR, status) {
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Click the button to start the dialog");
			}
		})
		
	});
	
	
	function distlayResponse(data) {
		$('.msg-insert').append("<div class='msg-receive'>"+ data["greeting_phrase"] +"</div>");
							
		for (var key in data["primary_answers"]) {
			var answer_phrase = formAnswerPhrase(data["primary_answers"][key]);							
			$('.msg-insert').append("<div class='msg-receive'>" + answer_phrase +"</div>");							
		}
		if (typeof data["additional_answers"] != "undefined") {
			if (data["additional_answers"].length > 0) {
				$('.msg-insert').append("<div class='msg-receive'>"+ data["additional_info_message"] +"</div>");						
				
				for (var key in data["additional_answers"]) {
					var current_phrase_additional = formAnswerPhrase(data["additional_answers"][key]);
					var name_key = "1";
					if ((typeof data["additional_answers"][key]["name"] != "undefined") && (data["additional_answers"][key]["name"] != "")) {
						name_key = data["additional_answers"][key]["name"];									
					} else if ((typeof data["additional_answers"][key]["entities_for_query"] != "undefined") && (data["additional_answers"][key]["name"] != {})) {
						if (typeof data["additional_answers"][key]["entities_for_query"]["inputEntity"] != "undefined") {
							name_key = data["additional_answers"][key]["entities_for_query"]["inputEntity"];

								if ((typeof data["additional_answers"][key]["content"] != "undefined") && (data["additional_answers"][key]["content"] != "")) {												
									name_key += " " + data["additional_answers"][key]["content"].slice(0, 20);
									if (data["additional_answers"][key]["content"].length > 20) {
										name_key += "... ";
									}
								} else {
									name_key += " " + String(key + 1);
								}
							
						}
					} else if ((typeof data["additional_answers"][key]["content"] != "undefined") && (data["additional_answers"][key]["content"] != "")) {
						name_key =  data["additional_answers"][key]["content"].slice(0, 20);
						if (data["additional_answers"][key]["content"].length > 20) {
										name_key += "... ";
									}
					}
					if (data["additional_answers"][key]["semantic_type"] == "sub_class") {
						name_key += " (components)";
					} else if (data["additional_answers"][key]["semantic_type"] == "label_definition") {	
						name_key += " (explanation)";
					} else if (data["additional_answers"][key]["semantic_type"] == "source") {	
						name_key += " (sources)";
					} else if (data["additional_answers"][key]["semantic_type"] == "measurement") {	
						name_key += " (measurement)";
					}
					
					
						additional_data[name_key] = current_phrase_additional;								
						$('.msg-insert').append("<div class='msg-receive'><button name='" + name_key + "' class='show-additional_button dialog-button'>" + name_key + "</button></div>");
										
				}
			}
		}	
		
		
	}
	
	
	
	
	
	
	

});