(function(){
  var c=document.getElementById('bmi-card');if(!c)return;
  var h=parseFloat(c.dataset.h),w=parseFloat(c.dataset.w);if(!h||!w)return;
  var bmi=w/Math.pow(h/100,2),t;
  if(bmi<18.5)t='Underweight';else if(bmi<25)t='Healthy range';else if(bmi<30)t='Overweight';else t='Obese range';
  document.getElementById('bmi-num').textContent=bmi.toFixed(1);
  document.getElementById('bmi-text').textContent=t;
  document.getElementById('bmi-dot').style.left=Math.min(100,Math.max(0,(bmi-15)/25*100))+'%';
  c.hidden=false;
})();
