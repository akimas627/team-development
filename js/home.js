$(document).ready(function () {
    $('#link_hobby').on('click', function () {
      $(window).scrollTop($('#hobby').position().top);
    });
});

//テキストを含む一般的なモーダル
$(".add_memo").modaal({
    overlay_close:true,//モーダル背景クリック時に閉じるか
    before_open:function(){// モーダルが開く前に行う動作
      $('html').css('overflow-y','hidden');/*縦スクロールバーを出さない*/
    },
    after_close:function(){// モーダルが閉じた後に行う動作
      $('html').css('overflow-y','scroll');/*縦スクロールバーを出す*/
    }
  });