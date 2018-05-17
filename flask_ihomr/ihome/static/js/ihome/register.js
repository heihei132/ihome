function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}
var imageCodeId = ""
var preImageCodeId = ""
// 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
function generateImageCode() {

    //获取随机字符串编号
    imageCodeId = generateUUID()

    //拼接一个访问路径
    image_url = "/api/v1.0/image_code?cur_id=" + imageCodeId + "&pre_id=" + preImageCodeId

    //将image_url设置到img标签中
    $(".image-code>img").attr("src",image_url)

    //记录上一次的imagecodeId
    preImageCodeId = imageCodeId
}

function sendSMSCode() {
    // 校验参数，保证输入框有数据填写
    $(".phonecode-a").removeAttr("onclick");
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    // TODO: 通过ajax方式向后端接口发送请求，让后端发送短信验证码
    // 拼接参数
    var params = {
        "mobile":mobile,
        "image_code": imageCode,
        "image_code_id": imageCodeId
    }

    //发送请求
    $.ajax({
        url: "/api/v1.0/sms_code",
        type: "POST",
        data: JSON.stringify(params),
        contentType:"application/json",
        headers : {"X-CSRFToken":getCookie("csrf_token")},
        success: function (data) {
            //1.判断请求是否成功
            if (data.errno == "0"){

                //定义变量
                num = 60;

                //开启定时器
                var t = setInterval(function () {
                    if (num == 1){
                        //清除定时器
                        clearInterval(t)

                        //设置内容,并且可以点击的状态
                        $(".phonecode-a").html("获取验证码")
                        $(".phonecode-a").attr("onclick","sendSMSCode()")

                    }else{
                        //每次减一秒
                        num -= 1;

                        //设置按钮的倒计时的值
                        $(".phonecode-a").html(num + "秒")
                    }
                },1000) //每秒钟执行一次
            }else{
                //更新图片验证码
                generateImageCode()

                //设置为可以重新点击状态
                $(".phonecode-a").attr("onclick","sendSMSCode()")

                //弹框提示
                alert(data.errmsg)
            }

        }
    })

}

$(document).ready(function() {
    generateImageCode();  // 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });

    // TODO: 注册的提交(判断参数是否为空)
     $(".form-register").submit(function (e) {
        e.preventDefault() //禁止表单的默认事件

        // 取到用户输入的内容
        var mobile = $("#mobile").val()
        var phonecode = $("#phonecode").val()
        var password = $("#password").val()
        var password2 = $("#password2").val()

        // 判断参数
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        }
        if (!phonecode) {
            $("#phone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return;
        }
        if (!password) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (password != password2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        // 参数拼接
        var params = {
            "mobile":mobile,
            "sms_code":phonecode,
            "password":password
        }

         // 发送post请求

        $.ajax({
            url:"/api/v1.0/user",
            type: "post",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            contentType: "application/json",
            success: function (resp) {
                if (resp.errno == "0"){
                    // 直接回到首页
                    location.href = "/index.html"
                }else {
                    $("#password2-err span").html(resp.errmsg)
                    $("#password2-err").show()
                }
            }
        })

    })


})
