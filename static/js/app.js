let zoom = 1;
function zoomPhoto(factor){
  const img=document.getElementById("photo");
  if(!img)return;
  zoom=Math.min(5,Math.max(.4,zoom*factor));
  img.style.transform=`scale(${zoom})`;
}
function toggleFullscreen(){
  const target=document.querySelector(".viewer-stage");
  if(!target)return;
  if(document.fullscreenElement) document.exitFullscreen();
  else target.requestFullscreen?.();
}
