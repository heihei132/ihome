function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){

    // TODO: 在页面加载完毕之后获取区域信息
    $.get("/api/v1.0/areas", function (resp) {
        if (resp.errno == "0") {
            var html = template("areas-tmpl", {"areas": resp.data})
            $("#area-id").html(html)
        }
    })


    // TODO: 处理房屋基本信息提交的表单数据
    $("#form-house-info").submit(function (e) {

        // 禁止表单的默认事件
        e.preventDefault()

        // 定义字典(对象)
        var params = {}

        // 取出了基本信息中所有的内容,拼接到params中
        $(this).serializeArray().map(function (x) {
            params[x.name] = x.value
        })

        // 拼接设施信息,存储到params
        var facilitys = []
        $(":checkbox:checked[name=facility]").each(function (i, x) {
            facilitys.push(x.value)
        })
        params["facility"] = facilitys // [1,3,4]
        $.ajax({
            url: "/api/v1.0/houses",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    //隐藏基本信息和设施信息
                    $("#form-house-info").hide()
                    //展示图片表单信息
                    $("#form-house-image").show()
                    // 在上传房屋基本信息成功之后，去设置房屋的id，以便在上传房屋图片的时候使用
                    $("#house-id").val(resp.data.house_id)
                }else if (resp.errno == "4101") {
                    location.href = "/login.html"
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })

    // TODO: 处理图片表单的数据
     $("#form-house-image").submit(function (e) {
        e.preventDefault()// 阻止表单默认事件
         // 取出房屋的编号
        var house_id = $("#house-id").val()

        $(this).ajaxSubmit({
            url: "/api/v1.0/houses/" + house_id + "/images",
            type: "put",
            headers:{
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    $(".house-image-cons").append('<img src="' + resp.data.url + '">')
                }
            }
        })
    })

})