function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}


function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // TODO: 查询用户的实名认证信息

    $.get("/api/v1.0/user/auth", function (resp) {
        if (resp.errno == "0") {
            // 判断是否有认证信息
            if (resp.data.real_name && resp.data.id_card) {
                // 设置值
                $("#real-name").val(resp.data.real_name)
                $("#id-card").val(resp.data.id_card)
                // 输入框置为不可点击
                $("#real-name").attr("disabled", true)
                $("#id-card").attr("disabled", true)
                // 隐藏保存按钮
                $(".btn-success").hide()
            }

        }else if (resp.errno == "4101") {
            location.href = "/login.html"
        }else {
            alert(resp.errmsg)
        }
    })


    // TODO: 管理实名信息表单的提交行为
    $("#form-auth").submit(function (e) {
         // 禁止表单的默认事件
        e.preventDefault()

         // 获取real-name, id_card标签中的值
        var real_name = $("#real-name").val()
        var id_card = $("#id-card").val()

        if (!(real_name && id_card)) {
            $(".error-msg").show()
            return
        }
        // 影藏错误的输入框
        $(".error-msg").hide()

        var params = {
            "real_name": real_name,
            "id_card": id_card
        }

        $.ajax({
            url: "/api/v1.0/user/auth",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    showSuccessMsg()
                    // 输入框置为不可点击
                    $("#real-name").prop("disabled", true)
                    $("#id-card").prop("disabled", true)
                    // 隐藏保存按钮
                    $(".btn-success").hide()
                }else if (resp.errno == "4101") {
                    location.href = "/login.html"
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })

})