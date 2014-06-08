var showLoadingIndicator = function(){
    $("body").html("<div class='loader'></div>");
};

$(document).ready(function(){
    $("a.thumbnail").click(function(){
	showLoadingIndicator();
    });
});
