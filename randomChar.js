/*get random string + timestamp*/
timestamp = timestamp/1000;
<script type="text/javascript">
function  randomChar(l)  {
var  x="0123456789qwertyuioplkjhgfdsazxcvbnm";
var  tmp="";
var timestamp = new Date().getTime();
for(var  i=0;i<  l;i++)  {
tmp  +=  x.charAt(Math.ceil(Math.random()*100000000)%x.length);
}
return  timestamp+tmp;
