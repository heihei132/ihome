//模态框居中的控制
function centerModals(){
    $('.modal').each(function(i){   //遍历每一个模态框
        var $clone = $(this).clone().css('display', 'block').appendTo('body');    
        var top = Math.round(($clone.height() - $clone.find('.modal-content').height()) / 2);
        top = top > 0 ? top : 0;
        $clone.remove();
        $(this).find('.modal-content').css("margin-top", top-30);  //修正原先已经有的30个像素
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    $('.modal').on('show.bs.modal', centerModals);      //当模态框出现的时候
    $(window).on('resize', centerModals);

    // TODO: 查询房客订单
    $.get("/api/v1.0/user/orders?role=custom", function (resp) {
        if (resp.errno == "0") {
            // 设置数据
            var html = template("orders-list-tmpl", {"orders": resp.data.orders})
            $(".orders-list").html(html)

            // 查询成功之后需要设置评论的相关处理
            $(".order-comment").on("click", function(){
                var orderId = $(this).parents("li").attr("order-id");
                $(".modal-comment").attr("order-id", orderId);
            });

            //点击评论后执行该函数
            $(".modal-comment").on('click', function () {
                var orderId = $(this).attr("order-id")
                // 评论
                var comment = $("#comment").val()
                $.ajax({
                    url: "/api/v1.0/orders/" + orderId + "/comment",
                    type: "put",
                    contentType: "application/json",
                    headers: {
                        "X-CSRFToken": getCookie("csrf_token")
                    },
                    data: JSON.stringify({"comment": comment}),
                    success: function (resp) {
                        $(".orders-list>li[order-id="+ orderId +"]>div.order-content>div.order-text>ul li:eq(4)>span").html("已完成");
                        $("ul.orders-list>li[order-id="+ orderId +"]>div.order-title>div.order-operate").hide();
                        $("#comment-modal").modal("hide");
                        location.reload()
                    }
                })

            })
        }else if(resp.errno == "4101") {
            location.href = "/"
        } else {
            alert(resp.errmsg)
        }
    })

});
