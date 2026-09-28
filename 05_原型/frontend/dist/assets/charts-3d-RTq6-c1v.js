import{i as $e,m as ki,A as ja,L as Za,p as Yn,R as Kn,g as Ya,r as Ka,e as bt,a as Qa,b as Ja,c as $a,d as eo,Z as to,f as Ci,h as ro,j as vr,k as Wi,l as io,n as no,o as ao,q as oo,s as so,S as Qn,t as Li,u as it,v as Ct,w as lo,x as Mr,y as Dr,C as Mi,z as Jn,B as uo,D as $n,E as ea,M as fo,F as ho,G as co,H as ta,I as ra,J as ia,K as vo,N as po,O as mo,P as _o,Q as go,T as yo}from"./charts-CHXwnOdI.js";function Xi(e,t,r){typeof t=="object"&&(r=t,t=null);var i=this,n;if(!(e instanceof Function)){n=[];for(var a in e)e.hasOwnProperty(a)&&n.push(a)}var o=function(l){if(i.apply(this,arguments),e instanceof Function?qi(this,e.call(this,l)):xo(this,e,n),this.constructor===o)for(var u=o.__initializers__,f=0;f<u.length;f++)u[f].apply(this,arguments)};o.__super__=i,i.__initializers__?o.__initializers__=i.__initializers__.slice():o.__initializers__=[],t&&o.__initializers__.push(t);var s=function(){};return s.prototype=i.prototype,o.prototype=new s,o.prototype.constructor=o,qi(o.prototype,r),o.extend=i.extend,o.derive=i.extend,o}function qi(e,t){if(t)for(var r in t)t.hasOwnProperty(r)&&(e[r]=t[r])}function xo(e,t,r){for(var i=0;i<r.length;i++){var n=r[i];e[n]=t[n]}}const To={extend:Xi,derive:Xi};function Eo(e,t){this.action=e,this.context=t}var Di={trigger:function(e){if(this.hasOwnProperty("__handlers__")&&this.__handlers__.hasOwnProperty(e)){var t=this.__handlers__[e],r=t.length,i=-1,n=arguments;switch(n.length){case 1:for(;++i<r;)t[i].action.call(t[i].context);return;case 2:for(;++i<r;)t[i].action.call(t[i].context,n[1]);return;case 3:for(;++i<r;)t[i].action.call(t[i].context,n[1],n[2]);return;case 4:for(;++i<r;)t[i].action.call(t[i].context,n[1],n[2],n[3]);return;case 5:for(;++i<r;)t[i].action.call(t[i].context,n[1],n[2],n[3],n[4]);return;default:for(;++i<r;)t[i].action.apply(t[i].context,Array.prototype.slice.call(n,1));return}}},on:function(e,t,r){if(!(!e||!t)){var i=this.__handlers__||(this.__handlers__={});if(!i[e])i[e]=[];else if(this.has(e,t))return;var n=new Eo(t,r||this);return i[e].push(n),this}},once:function(e,t,r){if(!e||!t)return;var i=this;function n(){i.off(e,n),t.apply(this,arguments)}return this.on(e,n,r)},before:function(e,t,r){if(!(!e||!t))return e="before"+e,this.on(e,t,r)},after:function(e,t,r){if(!(!e||!t))return e="after"+e,this.on(e,t,r)},success:function(e,t){return this.once("success",e,t)},error:function(e,t){return this.once("error",e,t)},off:function(e,t){var r=this.__handlers__||(this.__handlers__={});if(!t){r[e]=[];return}if(r[e]){for(var i=r[e],n=[],a=0;a<i.length;a++)t&&i[a].action!==t&&n.push(i[a]);r[e]=n}return this},has:function(e,t){var r=this.__handlers__;if(!r||!r[e])return!1;for(var i=r[e],n=0;n<i.length;n++)if(i[n].action===t)return!0}},So=0,wo=Array.prototype,bo=wo.forEach,he={genGUID:function(){return++So},relative2absolute:function(e,t){if(!t||e.match(/^\//))return e;for(var r=e.split("/"),i=t.split("/"),n=r[0];n==="."||n==="..";)n===".."&&i.pop(),r.shift(),n=r[0];return i.join("/")+"/"+r.join("/")},extend:function(e,t){if(t)for(var r in t)t.hasOwnProperty(r)&&(e[r]=t[r]);return e},defaults:function(e,t){if(t)for(var r in t)e[r]===void 0&&(e[r]=t[r]);return e},extendWithPropList:function(e,t,r){if(t)for(var i=0;i<r.length;i++){var n=r[i];e[n]=t[n]}return e},defaultsWithPropList:function(e,t,r){if(t)for(var i=0;i<r.length;i++){var n=r[i];e[n]==null&&(e[n]=t[n])}return e},each:function(e,t,r){if(e&&t)if(e.forEach&&e.forEach===bo)e.forEach(t,r);else if(e.length===+e.length)for(var i=0,n=e.length;i<n;i++)t.call(r,e[i],i,e);else for(var a in e)e.hasOwnProperty(a)&&t.call(r,e[a],a,e)},isObject:function(e){return e===Object(e)},isArray:function(e){return Array.isArray(e)},isArrayLike:function(e){return e?e.length===+e.length:!1},clone:function(e){if(he.isObject(e)){if(he.isArray(e))return e.slice();if(he.isArrayLike(e)){for(var t=new e.constructor(e.length),r=0;r<e.length;r++)t[r]=e[r];return t}else return he.extend({},e)}else return e}},be=function(){this.__uid__=he.genGUID()};be.__initializers__=[function(e){he.extend(this,e)}];he.extend(be,To);he.extend(be.prototype,Di);var ji=["OES_texture_float","OES_texture_half_float","OES_texture_float_linear","OES_texture_half_float_linear","OES_standard_derivatives","OES_vertex_array_object","OES_element_index_uint","WEBGL_compressed_texture_s3tc","WEBGL_depth_texture","EXT_texture_filter_anisotropic","EXT_shader_texture_lod","WEBGL_draw_buffers","EXT_frag_depth","EXT_sRGB","ANGLE_instanced_arrays"],Zi=["MAX_TEXTURE_SIZE","MAX_CUBE_MAP_TEXTURE_SIZE"];function Ao(e){for(var t={},r={},i=0;i<ji.length;i++){var n=ji[i];o(n)}for(var i=0;i<Zi.length;i++){var a=Zi[i];r[a]=e.getParameter(e[a])}this.getExtension=function(s){return s in t||o(s),t[s]},this.getParameter=function(s){return r[s]};function o(s){if(e.getExtension){var l=e.getExtension(s);l||(l=e.getExtension("MOZ_"+s)),l||(l=e.getExtension("WEBKIT_"+s)),t[s]=l}}}const L={DEPTH_BUFFER_BIT:256,STENCIL_BUFFER_BIT:1024,COLOR_BUFFER_BIT:16384,POINTS:0,LINES:1,LINE_LOOP:2,LINE_STRIP:3,TRIANGLES:4,TRIANGLE_STRIP:5,TRIANGLE_FAN:6,STREAM_DRAW:35040,STATIC_DRAW:35044,DYNAMIC_DRAW:35048,FRONT:1028,BACK:1029,FRONT_AND_BACK:1032,CW:2304,CCW:2305,BYTE:5120,UNSIGNED_BYTE:5121,SHORT:5122,UNSIGNED_SHORT:5123,INT:5124,UNSIGNED_INT:5125,FLOAT:5126,DEPTH_COMPONENT:6402,ALPHA:6406,RGB:6407,RGBA:6408,LUMINANCE:6409,LUMINANCE_ALPHA:6410,NEAREST:9728,LINEAR:9729,NEAREST_MIPMAP_NEAREST:9984,LINEAR_MIPMAP_NEAREST:9985,NEAREST_MIPMAP_LINEAR:9986,LINEAR_MIPMAP_LINEAR:9987,TEXTURE_2D:3553,TEXTURE_CUBE_MAP:34067,REPEAT:10497,CLAMP_TO_EDGE:33071,MIRRORED_REPEAT:33648,FRAMEBUFFER:36160,RENDERBUFFER:36161,DEPTH_STENCIL:34041,COLOR_ATTACHMENT0:36064,DEPTH_ATTACHMENT:36096,STENCIL_ATTACHMENT:36128,DEPTH_STENCIL_ATTACHMENT:33306};function Co(e){var t=new XMLHttpRequest;t.open("get",e.url),t.responseType=e.responseType||"text",e.onprogress&&(t.onprogress=function(r){if(r.lengthComputable){var i=r.loaded/r.total;e.onprogress(i,r.loaded,r.total)}else e.onprogress(null)}),t.onload=function(r){t.status>=400?e.onerror&&e.onerror():e.onload&&e.onload(t.response)},e.onerror&&(t.onerror=e.onerror),t.send(null)}const Lo={get:Co};var qr,Q={};Q.supportWebGL=function(){if(qr==null)try{var e=document.createElement("canvas"),t=e.getContext("webgl")||e.getContext("experimental-webgl");if(!t)throw new Error}catch{qr=!1}return qr};Q.Int8Array=typeof Int8Array>"u"?Array:Int8Array;Q.Uint8Array=typeof Uint8Array>"u"?Array:Uint8Array;Q.Uint16Array=typeof Uint16Array>"u"?Array:Uint16Array;Q.Uint32Array=typeof Uint32Array>"u"?Array:Uint32Array;Q.Int16Array=typeof Int16Array>"u"?Array:Int16Array;Q.Float32Array=typeof Float32Array>"u"?Array:Float32Array;Q.Float64Array=typeof Float64Array>"u"?Array:Float64Array;var Et={};typeof window<"u"?Et=window:typeof global<"u"&&(Et=global);Q.requestAnimationFrame=Et.requestAnimationFrame||Et.msRequestAnimationFrame||Et.mozRequestAnimationFrame||Et.webkitRequestAnimationFrame||function(e){setTimeout(e,16)};Q.createCanvas=function(){return document.createElement("canvas")};Q.createImage=function(){return new Et.Image};Q.request={get:Lo.get};Q.addEventListener=function(e,t,r,i){e.addEventListener(t,r,i)};Q.removeEventListener=function(e,t,r){e.removeEventListener(t,r)};var ye=function(){this.head=null,this.tail=null,this._length=0};ye.prototype.insert=function(e){var t=new ye.Entry(e);return this.insertEntry(t),t};ye.prototype.insertAt=function(e,t){if(!(e<0)){for(var r=this.head,i=0;r&&i!=e;)r=r.next,i++;if(r){var n=new ye.Entry(t),a=r.prev;a?(a.next=n,n.prev=a):this.head=n,n.next=r,r.prev=n}else this.insert(t)}};ye.prototype.insertBeforeEntry=function(e,t){var r=new ye.Entry(e),i=t.prev;i?(i.next=r,r.prev=i):this.head=r,r.next=t,t.prev=r,this._length++};ye.prototype.insertEntry=function(e){this.head?(this.tail.next=e,e.prev=this.tail,this.tail=e):this.head=this.tail=e,this._length++};ye.prototype.remove=function(e){var t=e.prev,r=e.next;t?t.next=r:this.head=r,r?r.prev=t:this.tail=t,e.next=e.prev=null,this._length--};ye.prototype.removeAt=function(e){if(!(e<0)){for(var t=this.head,r=0;t&&r!=e;)t=t.next,r++;if(t)return this.remove(t),t.value}};ye.prototype.getHead=function(){if(this.head)return this.head.value};ye.prototype.getTail=function(){if(this.tail)return this.tail.value};ye.prototype.getAt=function(e){if(!(e<0)){for(var t=this.head,r=0;t&&r!=e;)t=t.next,r++;return t.value}};ye.prototype.indexOf=function(e){for(var t=this.head,r=0;t;){if(t.value===e)return r;t=t.next,r++}};ye.prototype.length=function(){return this._length};ye.prototype.isEmpty=function(){return this._length===0};ye.prototype.forEach=function(e,t){for(var r=this.head,i=0,n=typeof t<"u";r;)n?e.call(t,r.value,i):e(r.value,i),r=r.next,i++};ye.prototype.clear=function(){this.tail=this.head=null,this._length=0};ye.Entry=function(e){this.value=e,this.next=null,this.prev=null};var Lt=function(e){this._list=new ye,this._map={},this._maxSize=e||10};Lt.prototype.setMaxSize=function(e){this._maxSize=e};Lt.prototype.put=function(e,t){if(!this._map.hasOwnProperty(e)){var r=this._list.length();if(r>=this._maxSize&&r>0){var i=this._list.head;this._list.remove(i),delete this._map[i.key]}var n=this._list.insert(t);n.key=e,this._map[e]=n}};Lt.prototype.get=function(e){var t=this._map[e];if(this._map.hasOwnProperty(e))return t!==this._list.tail&&(this._list.remove(t),this._list.insertEntry(t)),t.value};Lt.prototype.remove=function(e){var t=this._map[e];typeof t<"u"&&(delete this._map[e],this._list.remove(t))};Lt.prototype.clear=function(){this._list.clear(),this._map={}};var oe={},Yi={transparent:[0,0,0,0],aliceblue:[240,248,255,1],antiquewhite:[250,235,215,1],aqua:[0,255,255,1],aquamarine:[127,255,212,1],azure:[240,255,255,1],beige:[245,245,220,1],bisque:[255,228,196,1],black:[0,0,0,1],blanchedalmond:[255,235,205,1],blue:[0,0,255,1],blueviolet:[138,43,226,1],brown:[165,42,42,1],burlywood:[222,184,135,1],cadetblue:[95,158,160,1],chartreuse:[127,255,0,1],chocolate:[210,105,30,1],coral:[255,127,80,1],cornflowerblue:[100,149,237,1],cornsilk:[255,248,220,1],crimson:[220,20,60,1],cyan:[0,255,255,1],darkblue:[0,0,139,1],darkcyan:[0,139,139,1],darkgoldenrod:[184,134,11,1],darkgray:[169,169,169,1],darkgreen:[0,100,0,1],darkgrey:[169,169,169,1],darkkhaki:[189,183,107,1],darkmagenta:[139,0,139,1],darkolivegreen:[85,107,47,1],darkorange:[255,140,0,1],darkorchid:[153,50,204,1],darkred:[139,0,0,1],darksalmon:[233,150,122,1],darkseagreen:[143,188,143,1],darkslateblue:[72,61,139,1],darkslategray:[47,79,79,1],darkslategrey:[47,79,79,1],darkturquoise:[0,206,209,1],darkviolet:[148,0,211,1],deeppink:[255,20,147,1],deepskyblue:[0,191,255,1],dimgray:[105,105,105,1],dimgrey:[105,105,105,1],dodgerblue:[30,144,255,1],firebrick:[178,34,34,1],floralwhite:[255,250,240,1],forestgreen:[34,139,34,1],fuchsia:[255,0,255,1],gainsboro:[220,220,220,1],ghostwhite:[248,248,255,1],gold:[255,215,0,1],goldenrod:[218,165,32,1],gray:[128,128,128,1],green:[0,128,0,1],greenyellow:[173,255,47,1],grey:[128,128,128,1],honeydew:[240,255,240,1],hotpink:[255,105,180,1],indianred:[205,92,92,1],indigo:[75,0,130,1],ivory:[255,255,240,1],khaki:[240,230,140,1],lavender:[230,230,250,1],lavenderblush:[255,240,245,1],lawngreen:[124,252,0,1],lemonchiffon:[255,250,205,1],lightblue:[173,216,230,1],lightcoral:[240,128,128,1],lightcyan:[224,255,255,1],lightgoldenrodyellow:[250,250,210,1],lightgray:[211,211,211,1],lightgreen:[144,238,144,1],lightgrey:[211,211,211,1],lightpink:[255,182,193,1],lightsalmon:[255,160,122,1],lightseagreen:[32,178,170,1],lightskyblue:[135,206,250,1],lightslategray:[119,136,153,1],lightslategrey:[119,136,153,1],lightsteelblue:[176,196,222,1],lightyellow:[255,255,224,1],lime:[0,255,0,1],limegreen:[50,205,50,1],linen:[250,240,230,1],magenta:[255,0,255,1],maroon:[128,0,0,1],mediumaquamarine:[102,205,170,1],mediumblue:[0,0,205,1],mediumorchid:[186,85,211,1],mediumpurple:[147,112,219,1],mediumseagreen:[60,179,113,1],mediumslateblue:[123,104,238,1],mediumspringgreen:[0,250,154,1],mediumturquoise:[72,209,204,1],mediumvioletred:[199,21,133,1],midnightblue:[25,25,112,1],mintcream:[245,255,250,1],mistyrose:[255,228,225,1],moccasin:[255,228,181,1],navajowhite:[255,222,173,1],navy:[0,0,128,1],oldlace:[253,245,230,1],olive:[128,128,0,1],olivedrab:[107,142,35,1],orange:[255,165,0,1],orangered:[255,69,0,1],orchid:[218,112,214,1],palegoldenrod:[238,232,170,1],palegreen:[152,251,152,1],paleturquoise:[175,238,238,1],palevioletred:[219,112,147,1],papayawhip:[255,239,213,1],peachpuff:[255,218,185,1],peru:[205,133,63,1],pink:[255,192,203,1],plum:[221,160,221,1],powderblue:[176,224,230,1],purple:[128,0,128,1],red:[255,0,0,1],rosybrown:[188,143,143,1],royalblue:[65,105,225,1],saddlebrown:[139,69,19,1],salmon:[250,128,114,1],sandybrown:[244,164,96,1],seagreen:[46,139,87,1],seashell:[255,245,238,1],sienna:[160,82,45,1],silver:[192,192,192,1],skyblue:[135,206,235,1],slateblue:[106,90,205,1],slategray:[112,128,144,1],slategrey:[112,128,144,1],snow:[255,250,250,1],springgreen:[0,255,127,1],steelblue:[70,130,180,1],tan:[210,180,140,1],teal:[0,128,128,1],thistle:[216,191,216,1],tomato:[255,99,71,1],turquoise:[64,224,208,1],violet:[238,130,238,1],wheat:[245,222,179,1],white:[255,255,255,1],whitesmoke:[245,245,245,1],yellow:[255,255,0,1],yellowgreen:[154,205,50,1]};function We(e){return e=Math.round(e),e<0?0:e>255?255:e}function Mo(e){return e=Math.round(e),e<0?0:e>360?360:e}function sr(e){return e<0?0:e>1?1:e}function jr(e){return e.length&&e.charAt(e.length-1)==="%"?We(parseFloat(e)/100*255):We(parseInt(e,10))}function Ht(e){return e.length&&e.charAt(e.length-1)==="%"?sr(parseFloat(e)/100):sr(parseFloat(e))}function Zr(e,t,r){return r<0?r+=1:r>1&&(r-=1),r*6<1?e+(t-e)*r*6:r*2<1?t:r*3<2?e+(t-e)*(2/3-r)*6:e}function ct(e,t,r){return e+(t-e)*r}function ke(e,t,r,i,n){return e[0]=t,e[1]=r,e[2]=i,e[3]=n,e}function gi(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e}var na=new Lt(20),pr=null;function Dt(e,t){pr&&gi(pr,t),pr=na.put(e,pr||t.slice())}oe.parse=function(e,t){if(e){t=t||[];var r=na.get(e);if(r)return gi(t,r);e=e+"";var i=e.replace(/ /g,"").toLowerCase();if(i in Yi)return gi(t,Yi[i]),Dt(e,t),t;if(i.charAt(0)==="#"){if(i.length===4){var n=parseInt(i.substr(1),16);if(!(n>=0&&n<=4095)){ke(t,0,0,0,1);return}return ke(t,(n&3840)>>4|(n&3840)>>8,n&240|(n&240)>>4,n&15|(n&15)<<4,1),Dt(e,t),t}else if(i.length===7){var n=parseInt(i.substr(1),16);if(!(n>=0&&n<=16777215)){ke(t,0,0,0,1);return}return ke(t,(n&16711680)>>16,(n&65280)>>8,n&255,1),Dt(e,t),t}return}var a=i.indexOf("("),o=i.indexOf(")");if(a!==-1&&o+1===i.length){var s=i.substr(0,a),l=i.substr(a+1,o-(a+1)).split(","),u=1;switch(s){case"rgba":if(l.length!==4){ke(t,0,0,0,1);return}u=Ht(l.pop());case"rgb":if(l.length!==3){ke(t,0,0,0,1);return}return ke(t,jr(l[0]),jr(l[1]),jr(l[2]),u),Dt(e,t),t;case"hsla":if(l.length!==4){ke(t,0,0,0,1);return}return l[3]=Ht(l[3]),yi(l,t),Dt(e,t),t;case"hsl":if(l.length!==3){ke(t,0,0,0,1);return}return yi(l,t),Dt(e,t),t;default:return}}ke(t,0,0,0,1)}};oe.parseToFloat=function(e,t){if(t=oe.parse(e,t),!!t)return t[0]/=255,t[1]/=255,t[2]/=255,t};function yi(e,t){var r=(parseFloat(e[0])%360+360)%360/360,i=Ht(e[1]),n=Ht(e[2]),a=n<=.5?n*(i+1):n+i-n*i,o=n*2-a;return t=t||[],ke(t,We(Zr(o,a,r+1/3)*255),We(Zr(o,a,r)*255),We(Zr(o,a,r-1/3)*255),1),e.length===4&&(t[3]=e[3]),t}function Do(e){if(e){var t=e[0]/255,r=e[1]/255,i=e[2]/255,n=Math.min(t,r,i),a=Math.max(t,r,i),o=a-n,s=(a+n)/2,l,u;if(o===0)l=0,u=0;else{s<.5?u=o/(a+n):u=o/(2-a-n);var f=((a-t)/6+o/2)/o,h=((a-r)/6+o/2)/o,d=((a-i)/6+o/2)/o;t===a?l=d-h:r===a?l=1/3+f-d:i===a&&(l=2/3+h-f),l<0&&(l+=1),l>1&&(l-=1)}var c=[l*360,u,s];return e[3]!=null&&c.push(e[3]),c}}oe.lift=function(e,t){var r=oe.parse(e);if(r){for(var i=0;i<3;i++)t<0?r[i]=r[i]*(1-t)|0:r[i]=(255-r[i])*t+r[i]|0;return oe.stringify(r,r.length===4?"rgba":"rgb")}};oe.toHex=function(e){var t=oe.parse(e);if(t)return((1<<24)+(t[0]<<16)+(t[1]<<8)+ +t[2]).toString(16).slice(1)};oe.fastLerp=function(e,t,r){if(!(!(t&&t.length)||!(e>=0&&e<=1))){r=r||[];var i=e*(t.length-1),n=Math.floor(i),a=Math.ceil(i),o=t[n],s=t[a],l=i-n;return r[0]=We(ct(o[0],s[0],l)),r[1]=We(ct(o[1],s[1],l)),r[2]=We(ct(o[2],s[2],l)),r[3]=sr(ct(o[3],s[3],l)),r}};oe.fastMapToColor=oe.fastLerp;oe.lerp=function(e,t,r){if(!(!(t&&t.length)||!(e>=0&&e<=1))){var i=e*(t.length-1),n=Math.floor(i),a=Math.ceil(i),o=oe.parse(t[n]),s=oe.parse(t[a]),l=i-n,u=oe.stringify([We(ct(o[0],s[0],l)),We(ct(o[1],s[1],l)),We(ct(o[2],s[2],l)),sr(ct(o[3],s[3],l))],"rgba");return r?{color:u,leftIndex:n,rightIndex:a,value:i}:u}};oe.mapToColor=oe.lerp;oe.modifyHSL=function(e,t,r,i){if(e=oe.parse(e),e)return e=Do(e),t!=null&&(e[0]=Mo(t)),r!=null&&(e[1]=Ht(r)),i!=null&&(e[2]=Ht(i)),oe.stringify(yi(e),"rgba")};oe.modifyAlpha=function(e,t){if(e=oe.parse(e),e&&t!=null)return e[3]=sr(t),oe.stringify(e,"rgba")};oe.stringify=function(e,t){if(!(!e||!e.length)){var r=e[0]+","+e[1]+","+e[2];return(t==="rgba"||t==="hsva"||t==="hsla")&&(r+=","+e[3]),t+"("+r+")"}};var Po=oe.parseToFloat,Yr={};function Ki(e){var t=Object.keys(e);t.sort();for(var r=[],i=0;i<t.length;i++){var n=t[i],a=e[n];a===null?r.push(n):r.push(n+" "+a.toString())}return r.join(`
`)}function No(e,t,r){r.sort();for(var i=[],n=0;n<r.length;n++){var a=r[n];i.push(a)}var o=Ki(e)+`
`+Ki(t)+`
`+i.join(`
`);if(Yr[o])return Yr[o];var s=he.genGUID();return Yr[o]=s,s}var at=be.extend(function(){return{name:"",depthTest:!0,depthMask:!0,transparent:!1,blend:null,autoUpdateTextureStatus:!0,uniforms:{},vertexDefines:{},fragmentDefines:{},_textureStatus:{},_enabledUniforms:null}},function(){this.name||(this.name="MATERIAL_"+this.__uid__),this.shader&&this.attachShader(this.shader,!0)},{precision:"highp",setUniform:function(e,t){t===void 0&&console.warn('Uniform value "'+e+'" is undefined');var r=this.uniforms[e];r&&(typeof t=="string"&&(t=Po(t)||t),r.value=t,this.autoUpdateTextureStatus&&r.type==="t"&&(t?this.enableTexture(e):this.disableTexture(e)))},setUniforms:function(e){for(var t in e){var r=e[t];this.setUniform(t,r)}},isUniformEnabled:function(e){return this._enabledUniforms.indexOf(e)>=0},getEnabledUniforms:function(){return this._enabledUniforms},getTextureUniforms:function(){return this._textureUniforms},set:function(e,t){if(typeof e=="object")for(var r in e){var i=e[r];this.setUniform(r,i)}else this.setUniform(e,t)},get:function(e){var t=this.uniforms[e];if(t)return t.value},attachShader:function(e,t){var r=this.uniforms;this.uniforms=e.createUniforms(),this.shader=e;var i=this.uniforms;this._enabledUniforms=Object.keys(i),this._enabledUniforms.sort(),this._textureUniforms=this._enabledUniforms.filter(function(u){var f=this.uniforms[u].type;return f==="t"||f==="tv"},this);var n=this.vertexDefines,a=this.fragmentDefines;if(this.vertexDefines=he.clone(e.vertexDefines),this.fragmentDefines=he.clone(e.fragmentDefines),t){for(var o in r)i[o]&&(i[o].value=r[o].value);he.defaults(this.vertexDefines,n),he.defaults(this.fragmentDefines,a)}var s={};for(var l in e.textures)s[l]={shaderType:e.textures[l].shaderType,type:e.textures[l].type,enabled:t&&this._textureStatus[l]?this._textureStatus[l].enabled:!1};this._textureStatus=s,this._programKey=""},clone:function(){var e=new this.constructor({name:this.name,shader:this.shader});for(var t in this.uniforms)e.uniforms[t].value=this.uniforms[t].value;return e.depthTest=this.depthTest,e.depthMask=this.depthMask,e.transparent=this.transparent,e.blend=this.blend,e.vertexDefines=he.clone(this.vertexDefines),e.fragmentDefines=he.clone(this.fragmentDefines),e.enableTexture(this.getEnabledTextures()),e.precision=this.precision,e},define:function(e,t,r){var i=this.vertexDefines,n=this.fragmentDefines;e!=="vertex"&&e!=="fragment"&&e!=="both"&&arguments.length<3&&(r=t,t=e,e="both"),r=r??null,(e==="vertex"||e==="both")&&i[t]!==r&&(i[t]=r,this._programKey=""),(e==="fragment"||e==="both")&&n[t]!==r&&(n[t]=r,e!=="both"&&(this._programKey=""))},undefine:function(e,t){e!=="vertex"&&e!=="fragment"&&e!=="both"&&arguments.length<2&&(t=e,e="both"),(e==="vertex"||e==="both")&&this.isDefined("vertex",t)&&(delete this.vertexDefines[t],this._programKey=""),(e==="fragment"||e==="both")&&this.isDefined("fragment",t)&&(delete this.fragmentDefines[t],e!=="both"&&(this._programKey=""))},isDefined:function(e,t){switch(e){case"vertex":return this.vertexDefines[t]!==void 0;case"fragment":return this.fragmentDefines[t]!==void 0}},getDefine:function(e,t){switch(e){case"vertex":return this.vertexDefines[t];case"fragment":return this.fragmentDefines[t]}},enableTexture:function(e){if(Array.isArray(e)){for(var t=0;t<e.length;t++)this.enableTexture(e[t]);return}var r=this._textureStatus[e];if(r){var i=r.enabled;i||(r.enabled=!0,this._programKey="")}},enableTexturesAll:function(){var e=this._textureStatus;for(var t in e)e[t].enabled=!0;this._programKey=""},disableTexture:function(e){if(Array.isArray(e)){for(var t=0;t<e.length;t++)this.disableTexture(e[t]);return}var r=this._textureStatus[e];if(r){var i=!r.enabled;i||(r.enabled=!1,this._programKey="")}},disableTexturesAll:function(){var e=this._textureStatus;for(var t in e)e[t].enabled=!1;this._programKey=""},isTextureEnabled:function(e){var t=this._textureStatus;return!!t[e]&&t[e].enabled},getEnabledTextures:function(){var e=[],t=this._textureStatus;for(var r in t)t[r].enabled&&e.push(r);return e},dirtyDefines:function(){this._programKey=""},getProgramKey:function(){return this._programKey||(this._programKey=No(this.vertexDefines,this.fragmentDefines,this.getEnabledTextures())),this._programKey}}),Cr=1e-6,Se=Array,Ut=Math.random,P={};P.create=function(){var e=new Se(2);return e[0]=0,e[1]=0,e};P.clone=function(e){var t=new Se(2);return t[0]=e[0],t[1]=e[1],t};P.fromValues=function(e,t){var r=new Se(2);return r[0]=e,r[1]=t,r};P.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e};P.set=function(e,t,r){return e[0]=t,e[1]=r,e};P.add=function(e,t,r){return e[0]=t[0]+r[0],e[1]=t[1]+r[1],e};P.subtract=function(e,t,r){return e[0]=t[0]-r[0],e[1]=t[1]-r[1],e};P.sub=P.subtract;P.multiply=function(e,t,r){return e[0]=t[0]*r[0],e[1]=t[1]*r[1],e};P.mul=P.multiply;P.divide=function(e,t,r){return e[0]=t[0]/r[0],e[1]=t[1]/r[1],e};P.div=P.divide;P.min=function(e,t,r){return e[0]=Math.min(t[0],r[0]),e[1]=Math.min(t[1],r[1]),e};P.max=function(e,t,r){return e[0]=Math.max(t[0],r[0]),e[1]=Math.max(t[1],r[1]),e};P.scale=function(e,t,r){return e[0]=t[0]*r,e[1]=t[1]*r,e};P.scaleAndAdd=function(e,t,r,i){return e[0]=t[0]+r[0]*i,e[1]=t[1]+r[1]*i,e};P.distance=function(e,t){var r=t[0]-e[0],i=t[1]-e[1];return Math.sqrt(r*r+i*i)};P.dist=P.distance;P.squaredDistance=function(e,t){var r=t[0]-e[0],i=t[1]-e[1];return r*r+i*i};P.sqrDist=P.squaredDistance;P.length=function(e){var t=e[0],r=e[1];return Math.sqrt(t*t+r*r)};P.len=P.length;P.squaredLength=function(e){var t=e[0],r=e[1];return t*t+r*r};P.sqrLen=P.squaredLength;P.negate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e};P.inverse=function(e,t){return e[0]=1/t[0],e[1]=1/t[1],e};P.normalize=function(e,t){var r=t[0],i=t[1],n=r*r+i*i;return n>0&&(n=1/Math.sqrt(n),e[0]=t[0]*n,e[1]=t[1]*n),e};P.dot=function(e,t){return e[0]*t[0]+e[1]*t[1]};P.cross=function(e,t,r){var i=t[0]*r[1]-t[1]*r[0];return e[0]=e[1]=0,e[2]=i,e};P.lerp=function(e,t,r,i){var n=t[0],a=t[1];return e[0]=n+i*(r[0]-n),e[1]=a+i*(r[1]-a),e};P.random=function(e,t){t=t||1;var r=GLMAT_RANDOM()*2*Math.PI;return e[0]=Math.cos(r)*t,e[1]=Math.sin(r)*t,e};P.transformMat2=function(e,t,r){var i=t[0],n=t[1];return e[0]=r[0]*i+r[2]*n,e[1]=r[1]*i+r[3]*n,e};P.transformMat2d=function(e,t,r){var i=t[0],n=t[1];return e[0]=r[0]*i+r[2]*n+r[4],e[1]=r[1]*i+r[3]*n+r[5],e};P.transformMat3=function(e,t,r){var i=t[0],n=t[1];return e[0]=r[0]*i+r[3]*n+r[6],e[1]=r[1]*i+r[4]*n+r[7],e};P.transformMat4=function(e,t,r){var i=t[0],n=t[1];return e[0]=r[0]*i+r[4]*n+r[12],e[1]=r[1]*i+r[5]*n+r[13],e};P.forEach=(function(){var e=P.create();return function(t,r,i,n,a,o){var s,l;for(r||(r=2),i||(i=0),n?l=Math.min(n*r+i,t.length):l=t.length,s=i;s<l;s+=r)e[0]=t[s],e[1]=t[s+1],a(e,e,o),t[s]=e[0],t[s+1]=e[1];return t}})();var W=function(e,t){e=e||0,t=t||0,this.array=P.fromValues(e,t),this._dirty=!0};W.prototype={constructor:W,add:function(e){return P.add(this.array,this.array,e.array),this._dirty=!0,this},set:function(e,t){return this.array[0]=e,this.array[1]=t,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this._dirty=!0,this},clone:function(){return new W(this.x,this.y)},copy:function(e){return P.copy(this.array,e.array),this._dirty=!0,this},cross:function(e,t){return P.cross(e.array,this.array,t.array),e._dirty=!0,this},dist:function(e){return P.dist(this.array,e.array)},distance:function(e){return P.distance(this.array,e.array)},div:function(e){return P.div(this.array,this.array,e.array),this._dirty=!0,this},divide:function(e){return P.divide(this.array,this.array,e.array),this._dirty=!0,this},dot:function(e){return P.dot(this.array,e.array)},len:function(){return P.len(this.array)},length:function(){return P.length(this.array)},lerp:function(e,t,r){return P.lerp(this.array,e.array,t.array,r),this._dirty=!0,this},min:function(e){return P.min(this.array,this.array,e.array),this._dirty=!0,this},max:function(e){return P.max(this.array,this.array,e.array),this._dirty=!0,this},mul:function(e){return P.mul(this.array,this.array,e.array),this._dirty=!0,this},multiply:function(e){return P.multiply(this.array,this.array,e.array),this._dirty=!0,this},negate:function(){return P.negate(this.array,this.array),this._dirty=!0,this},normalize:function(){return P.normalize(this.array,this.array),this._dirty=!0,this},random:function(e){return P.random(this.array,e),this._dirty=!0,this},scale:function(e){return P.scale(this.array,this.array,e),this._dirty=!0,this},scaleAndAdd:function(e,t){return P.scaleAndAdd(this.array,this.array,e.array,t),this._dirty=!0,this},sqrDist:function(e){return P.sqrDist(this.array,e.array)},squaredDistance:function(e){return P.squaredDistance(this.array,e.array)},sqrLen:function(){return P.sqrLen(this.array)},squaredLength:function(){return P.squaredLength(this.array)},sub:function(e){return P.sub(this.array,this.array,e.array),this._dirty=!0,this},subtract:function(e){return P.subtract(this.array,this.array,e.array),this._dirty=!0,this},transformMat2:function(e){return P.transformMat2(this.array,this.array,e.array),this._dirty=!0,this},transformMat2d:function(e){return P.transformMat2d(this.array,this.array,e.array),this._dirty=!0,this},transformMat3:function(e){return P.transformMat3(this.array,this.array,e.array),this._dirty=!0,this},transformMat4:function(e){return P.transformMat4(this.array,this.array,e.array),this._dirty=!0,this},toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};if(Object.defineProperty){var Qi=W.prototype;Object.defineProperty(Qi,"x",{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),Object.defineProperty(Qi,"y",{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}})}W.add=function(e,t,r){return P.add(e.array,t.array,r.array),e._dirty=!0,e};W.set=function(e,t,r){return P.set(e.array,t,r),e._dirty=!0,e};W.copy=function(e,t){return P.copy(e.array,t.array),e._dirty=!0,e};W.cross=function(e,t,r){return P.cross(e.array,t.array,r.array),e._dirty=!0,e};W.dist=function(e,t){return P.distance(e.array,t.array)};W.distance=W.dist;W.div=function(e,t,r){return P.divide(e.array,t.array,r.array),e._dirty=!0,e};W.divide=W.div;W.dot=function(e,t){return P.dot(e.array,t.array)};W.len=function(e){return P.length(e.array)};W.lerp=function(e,t,r,i){return P.lerp(e.array,t.array,r.array,i),e._dirty=!0,e};W.min=function(e,t,r){return P.min(e.array,t.array,r.array),e._dirty=!0,e};W.max=function(e,t,r){return P.max(e.array,t.array,r.array),e._dirty=!0,e};W.mul=function(e,t,r){return P.multiply(e.array,t.array,r.array),e._dirty=!0,e};W.multiply=W.mul;W.negate=function(e,t){return P.negate(e.array,t.array),e._dirty=!0,e};W.normalize=function(e,t){return P.normalize(e.array,t.array),e._dirty=!0,e};W.random=function(e,t){return P.random(e.array,t),e._dirty=!0,e};W.scale=function(e,t,r){return P.scale(e.array,t.array,r),e._dirty=!0,e};W.scaleAndAdd=function(e,t,r,i){return P.scaleAndAdd(e.array,t.array,r.array,i),e._dirty=!0,e};W.sqrDist=function(e,t){return P.sqrDist(e.array,t.array)};W.squaredDistance=W.sqrDist;W.sqrLen=function(e){return P.sqrLen(e.array)};W.squaredLength=W.sqrLen;W.sub=function(e,t,r){return P.subtract(e.array,t.array,r.array),e._dirty=!0,e};W.subtract=W.sub;W.transformMat2=function(e,t,r){return P.transformMat2(e.array,t.array,r.array),e._dirty=!0,e};W.transformMat2d=function(e,t,r){return P.transformMat2d(e.array,t.array,r.array),e._dirty=!0,e};W.transformMat3=function(e,t,r){return P.transformMat3(e.array,t.array,r.array),e._dirty=!0,e};W.transformMat4=function(e,t,r){return P.transformMat4(e.array,t.array,r.array),e._dirty=!0,e};var Ji=1,$i=2,Kr=3,en={};function Ro(e){for(var t=e.split(`
`),r=0,i=t.length;r<i;r++)t[r]=r+1+": "+t[r];return t.join(`
`)}function tn(e,t,r){if(!e.getShaderParameter(t,e.COMPILE_STATUS))return[e.getShaderInfoLog(t),Ro(r)].join(`
`)}var rn=new Q.Float32Array(16),Oo=be.extend({uniformSemantics:{},attributes:{}},function(){this._locations={},this._textureSlot=0,this._program=null},{bind:function(e){this._textureSlot=0,e.gl.useProgram(this._program)},hasUniform:function(e){var t=this._locations[e];return t!=null},useTextureSlot:function(e,t,r){t&&(e.gl.activeTexture(e.gl.TEXTURE0+r),t.isRenderable()?t.bind(e):t.unbind(e))},currentTextureSlot:function(){return this._textureSlot},resetTextureSlot:function(e){this._textureSlot=e||0},takeCurrentTextureSlot:function(e,t){var r=this._textureSlot;return this.useTextureSlot(e,t,r),this._textureSlot++,r},setUniform:function(e,t,r,i){var n=this._locations,a=n[r];if(a==null)return!1;switch(t){case"m4":if(!(i instanceof Float32Array)){for(var o=0;o<i.length;o++)rn[o]=i[o];i=rn}e.uniformMatrix4fv(a,!1,i);break;case"2i":e.uniform2i(a,i[0],i[1]);break;case"2f":e.uniform2f(a,i[0],i[1]);break;case"3i":e.uniform3i(a,i[0],i[1],i[2]);break;case"3f":e.uniform3f(a,i[0],i[1],i[2]);break;case"4i":e.uniform4i(a,i[0],i[1],i[2],i[3]);break;case"4f":e.uniform4f(a,i[0],i[1],i[2],i[3]);break;case"1i":e.uniform1i(a,i);break;case"1f":e.uniform1f(a,i);break;case"1fv":e.uniform1fv(a,i);break;case"1iv":e.uniform1iv(a,i);break;case"2iv":e.uniform2iv(a,i);break;case"2fv":e.uniform2fv(a,i);break;case"3iv":e.uniform3iv(a,i);break;case"3fv":e.uniform3fv(a,i);break;case"4iv":e.uniform4iv(a,i);break;case"4fv":e.uniform4fv(a,i);break;case"m2":case"m2v":e.uniformMatrix2fv(a,!1,i);break;case"m3":case"m3v":e.uniformMatrix3fv(a,!1,i);break;case"m4v":if(Array.isArray(i)&&Array.isArray(i[0])){for(var s=new Q.Float32Array(i.length*16),l=0,o=0;o<i.length;o++)for(var u=i[o],f=0;f<16;f++)s[l++]=u[f];e.uniformMatrix4fv(a,!1,s)}else e.uniformMatrix4fv(a,!1,i);break}return!0},setUniformOfSemantic:function(e,t,r){var i=this.uniformSemantics[t];return i?this.setUniform(e,i.type,i.symbol,r):!1},enableAttributes:function(e,t,r){var i=e.gl,n=this._program,a=this._locations,o;r?o=r.__enabledAttributeList:o=en[e.__uid__],o||(r?o=r.__enabledAttributeList=[]:o=en[e.__uid__]=[]);for(var s=[],l=0;l<t.length;l++){var u=t[l];if(!this.attributes[u]){s[l]=-1;continue}var f=a[u];if(f==null){if(f=i.getAttribLocation(n,u),f===-1){s[l]=-1;continue}a[u]=f}s[l]=f,o[f]?o[f]=$i:o[f]=Ji}for(var l=0;l<o.length;l++)switch(o[l]){case Ji:i.enableVertexAttribArray(l),o[l]=Kr;break;case $i:o[l]=Kr;break;case Kr:i.disableVertexAttribArray(l),o[l]=0;break}return s},getAttribLocation:function(e,t){var r=this._locations,i=r[t];return i==null&&(i=e.getAttribLocation(this._program,t),r[t]=i),i},buildProgram:function(e,t,r,i){var n=e.createShader(e.VERTEX_SHADER),a=e.createProgram();e.shaderSource(n,r),e.compileShader(n);var o=e.createShader(e.FRAGMENT_SHADER);e.shaderSource(o,i),e.compileShader(o);var s=tn(e,n,r);if(s||(s=tn(e,o,i),s))return s;if(e.attachShader(a,n),e.attachShader(a,o),t.attributeSemantics.POSITION)e.bindAttribLocation(a,0,t.attributeSemantics.POSITION.symbol);else{var l=Object.keys(this.attributes);e.bindAttribLocation(a,0,l[0])}if(e.linkProgram(a),e.deleteShader(n),e.deleteShader(o),this._program=a,this.vertexCode=r,this.fragmentCode=i,!e.getProgramParameter(a,e.LINK_STATUS))return`Could not link program
`+e.getProgramInfoLog(a);for(var u=0;u<t.uniforms.length;u++){var f=t.uniforms[u];this._locations[f]=e.getUniformLocation(a,f)}}}),Io=/for\s*?\(int\s*?_idx_\s*\=\s*([\w-]+)\;\s*_idx_\s*<\s*([\w-]+);\s*_idx_\s*\+\+\s*\)\s*\{\{([\s\S]+?)(?=\}\})\}\}/g;function nn(e,t,r){function i(o,s,l,u){var f="";isNaN(s)&&(s in t?s=t[s]:s=n[s]),isNaN(l)&&(l in t?l=t[l]:l=n[l]);for(var h=parseInt(s);h<parseInt(l);h++)f+="{"+u.replace(/float\s*\(\s*_idx_\s*\)/g,h.toFixed(1)).replace(/_idx_/g,h)+"}";return f}var n={};for(var a in r)n[a+"_COUNT"]=r[a];return e.replace(Io,i)}function Qr(e,t,r){var i=[];if(t)for(var n in t){var a=t[n];a>0&&i.push("#define "+n.toUpperCase()+"_COUNT "+a)}if(r)for(var o=0;o<r.length;o++){var s=r[o];i.push("#define "+s.toUpperCase()+"_ENABLED")}for(var s in e){var l=e[s];l===null?i.push("#define "+s):i.push("#define "+s+" "+l.toString())}return i.join(`
`)}function Bo(e){for(var t=[],r=0;r<e.length;r++)t.push("#extension GL_"+e[r]+" : enable");return t.join(`
`)}function Fo(e){return["precision",e,"float"].join(" ")+`;
`+["precision",e,"int"].join(" ")+`;
`+["precision",e,"sampler2D"].join(" ")+`;
`}function aa(e){this._renderer=e,this._cache={}}aa.prototype.getProgram=function(e,t,r){var i=this._cache,n=e.isSkinnedMesh&&e.isSkinnedMesh(),a=e.isInstancedMesh&&e.isInstancedMesh(),o="s"+t.shader.shaderID+"m"+t.getProgramKey();r&&(o+="se"+r.getProgramKey(e.lightGroup)),n&&(o+=",sk"+e.joints.length),a&&(o+=",is");var g=i[o];if(g)return g;var s=r?r.getLightsNumbers(e.lightGroup):{},l=this._renderer,u=l.gl,f=t.getEnabledTextures(),h="";if(n){var d={SKINNING:null,JOINT_COUNT:e.joints.length};e.joints.length>l.getMaxJointNumber()&&(d.USE_SKIN_MATRICES_TEXTURE=null),h+=`
`+Qr(d)+`
`}a&&(h+=`
#define INSTANCING
`);var c=h+Qr(t.vertexDefines,s,f),v=h+Qr(t.fragmentDefines,s,f),p=c+`
`+t.shader.vertex,m=["OES_standard_derivatives","EXT_shader_texture_lod"].filter(function(S){return l.getGLExtension(S)!=null});m.indexOf("EXT_shader_texture_lod")>=0&&(v+=`
#define SUPPORT_TEXTURE_LOD`),m.indexOf("OES_standard_derivatives")>=0&&(v+=`
#define SUPPORT_STANDARD_DERIVATIVES`);var _=Bo(m)+`
`+Fo(t.precision)+`
`+v+`
`+t.shader.fragment,x=nn(p,t.vertexDefines,s),T=nn(_,t.fragmentDefines,s),g=new Oo;g.uniformSemantics=t.shader.uniformSemantics,g.attributes=t.shader.attributes;var E=g.buildProgram(u,t.shader,x,T);return g.__error=E,i[o]=g,g};var an=/uniform\s+(bool|float|int|vec2|vec3|vec4|ivec2|ivec3|ivec4|mat2|mat3|mat4|sampler2D|samplerCube)\s+([\s\S]*?);/g,Uo=/attribute\s+(float|int|vec2|vec3|vec4)\s+([\s\S]*?);/g,on=/#define\s+(\w+)?(\s+[\d-.]+)?\s*;?\s*\n/g,zo={bool:"1i",int:"1i",sampler2D:"t",samplerCube:"t",float:"1f",vec2:"2f",vec3:"3f",vec4:"4f",ivec2:"2i",ivec3:"3i",ivec4:"4i",mat2:"m2",mat3:"m3",mat4:"m4"};function et(e){for(var t=[],r=0;r<e;r++)t[r]=0;return t}var sn={bool:function(){return!0},int:function(){return 0},float:function(){return 0},sampler2D:function(){return null},samplerCube:function(){return null},vec2:function(){return et(2)},vec3:function(){return et(3)},vec4:function(){return et(4)},ivec2:function(){return et(2)},ivec3:function(){return et(3)},ivec4:function(){return et(4)},mat2:function(){return et(4)},mat3:function(){return et(9)},mat4:function(){return et(16)},array:function(){return[]}},xi=["POSITION","NORMAL","BINORMAL","TANGENT","TEXCOORD","TEXCOORD_0","TEXCOORD_1","COLOR","JOINT","WEIGHT"],oa=["SKIN_MATRIX","VIEWPORT_SIZE","VIEWPORT","DEVICEPIXELRATIO","WINDOW_SIZE","NEAR","FAR","TIME"],sa=["WORLD","VIEW","PROJECTION","WORLDVIEW","VIEWPROJECTION","WORLDVIEWPROJECTION","WORLDINVERSE","VIEWINVERSE","PROJECTIONINVERSE","WORLDVIEWINVERSE","VIEWPROJECTIONINVERSE","WORLDVIEWPROJECTIONINVERSE","WORLDTRANSPOSE","VIEWTRANSPOSE","PROJECTIONTRANSPOSE","WORLDVIEWTRANSPOSE","VIEWPROJECTIONTRANSPOSE","WORLDVIEWPROJECTIONTRANSPOSE","WORLDINVERSETRANSPOSE","VIEWINVERSETRANSPOSE","PROJECTIONINVERSETRANSPOSE","WORLDVIEWINVERSETRANSPOSE","VIEWPROJECTIONINVERSETRANSPOSE","WORLDVIEWPROJECTIONINVERSETRANSPOSE"],Ho={vec4:4,vec3:3,vec2:2,float:1},Jr={},la={};function Vo(e,t){var r="vertex:"+e+"fragment:"+t;if(Jr[r])return Jr[r];var i=he.genGUID();return Jr[r]=i,la[i]={vertex:e,fragment:t},i}function ln(e){return e.replace(/[ \t]*\/\/.*\n/g,"").replace(/[ \t]*\/\*[\s\S]*?\*\//g,"")}function Pt(){console.error("Wrong uniform/attributes syntax")}function un(e,t){for(var r=/[,=\(\):]/,i=t.replace(/:\s*\[\s*(.*)\s*\]/g,"="+e+"($1)").replace(/\s+/g,"").split(/(?=[,=\(\):])/g),n=[],a=0;a<i.length;a++)i[a].match(r)?n.push(i[a].charAt(0),i[a].slice(1)):n.push(i[a]);i=n;var o=0,s=1,l=2,u=3,f=4,h=5,d=o,c={},v=null,p;m(i[0]);function m(T){T||Pt();var g=T.match(/\[(.*?)\]/);p=T.replace(/\[(.*?)\]/,""),c[p]={},g&&(c[p].isArray=!0,c[p].arraySize=g[1])}for(var a=1;a<i.length;a++){var _=i[a];if(_){if(_==="="){if(d!==o&&d!==u){Pt();break}d=s;continue}else if(_===":"){d=f;continue}else if(_===","){if(d===l){if(!(v instanceof Array)){Pt();break}v.push(+i[++a])}else d=h;continue}else if(_===")"){c[p].value=new Q.Float32Array(v),v=null,d=h;continue}else if(_==="("){if(d!==l){Pt();break}if(!(v instanceof Array)){Pt();break}v.push(+i[++a]);continue}else if(_.indexOf("vec")>=0){if(d!==s&&d!==f){Pt();break}d=l,v=[];continue}else if(d===s){e==="bool"?c[p].value=_==="true":c[p].value=parseFloat(_),v=null;continue}else if(d===f){var x=_;xi.indexOf(x)>=0||oa.indexOf(x)>=0||sa.indexOf(x)>=0?c[p].semantic=x:x==="ignore"||x==="unconfigurable"?c[p].ignore=!0:e==="bool"?c[p].value=x==="true":c[p].value=parseFloat(x);continue}m(_),d=o}}return c}function z(e,t){typeof e=="object"&&(t=e.fragment,e=e.vertex),e=ln(e),t=ln(t),this._shaderID=Vo(e,t),this._vertexCode=z.parseImport(e),this._fragmentCode=z.parseImport(t),this.attributeSemantics={},this.matrixSemantics={},this.uniformSemantics={},this.matrixSemanticKeys=[],this.uniformTemplates={},this.attributes={},this.textures={},this.vertexDefines={},this.fragmentDefines={},this._parseAttributes(),this._parseUniforms(),this._parseDefines()}z.prototype={constructor:z,createUniforms:function(){var e={};for(var t in this.uniformTemplates){var r=this.uniformTemplates[t];e[t]={type:r.type,value:r.value()}}return e},_parseImport:function(){this._vertexCode=z.parseImport(this.vertex),this._fragmentCode=z.parseImport(this.fragment)},_addSemanticUniform:function(e,t,r){if(xi.indexOf(r)>=0)this.attributeSemantics[r]={symbol:e,type:t};else if(sa.indexOf(r)>=0){var i=!1,n=r;r.match(/TRANSPOSE$/)&&(i=!0,n=r.slice(0,-9)),this.matrixSemantics[r]={symbol:e,type:t,isTranspose:i,semanticNoTranspose:n}}else oa.indexOf(r)>=0&&(this.uniformSemantics[r]={symbol:e,type:t})},_addMaterialUniform:function(e,t,r,i,n,a){a[e]={type:r,value:n?sn.array:i||sn[t],semantic:null}},_parseUniforms:function(){var e={},t=this,r="vertex";this._uniformList=[],this._vertexCode=this._vertexCode.replace(an,n),r="fragment",this._fragmentCode=this._fragmentCode.replace(an,n),t.matrixSemanticKeys=Object.keys(this.matrixSemantics);function i(a){return a!=null?function(){return a}:null}function n(a,o,s){var l=un(o,s),u=[];for(var f in l){var h=l[f],d=h.semantic,c=f,v=zo[o],p=i(l[f].value);l[f].isArray&&(c+="["+l[f].arraySize+"]",v+="v"),u.push(c),t._uniformList.push(f),h.ignore||((o==="sampler2D"||o==="samplerCube")&&(t.textures[f]={shaderType:r,type:o}),d?t._addSemanticUniform(f,v,d):t._addMaterialUniform(f,o,v,p,l[f].isArray,e))}return u.length>0?"uniform "+o+" "+u.join(",")+`;
`:""}this.uniformTemplates=e},_parseAttributes:function(){var e={},t=this;this._vertexCode=this._vertexCode.replace(Uo,r);function r(i,n,a){var o=un(n,a),s=Ho[n]||1,l=[];for(var u in o){var f=o[u].semantic;if(e[u]={type:"float",size:s,semantic:f||null},f){if(xi.indexOf(f)<0)throw new Error('Unkown semantic "'+f+'"');t.attributeSemantics[f]={symbol:u,type:n}}l.push(u)}return"attribute "+n+" "+l.join(",")+`;
`}this.attributes=e},_parseDefines:function(){var e=this,t="vertex";this._vertexCode=this._vertexCode.replace(on,r),t="fragment",this._fragmentCode=this._fragmentCode.replace(on,r);function r(i,n,a){var o=t==="vertex"?e.vertexDefines:e.fragmentDefines;return o[n]||(a==="false"?o[n]=!1:a==="true"?o[n]=!0:o[n]=a?isNaN(parseFloat(a))?a.trim():parseFloat(a):null),""}},clone:function(){var e=la[this._shaderID],t=new z(e.vertex,e.fragment);return t}};Object.defineProperty&&(Object.defineProperty(z.prototype,"shaderID",{get:function(){return this._shaderID}}),Object.defineProperty(z.prototype,"vertex",{get:function(){return this._vertexCode}}),Object.defineProperty(z.prototype,"fragment",{get:function(){return this._fragmentCode}}),Object.defineProperty(z.prototype,"uniforms",{get:function(){return this._uniformList}}));var Go=/(@import)\s*([0-9a-zA-Z_\-\.]*)/g;z.parseImport=function(e){return e=e.replace(Go,function(n,r,i){var n=z.source(i);return n?z.parseImport(n):(console.error('Shader chunk "'+i+'" not existed in library'),"")}),e};var ko=/(@export)\s*([0-9a-zA-Z_\-\.]*)\s*\n([\s\S]*?)@end/g;z.import=function(e){e.replace(ko,function(t,r,i,a){var a=a.replace(/(^[\s\t\xa0\u3000]+)|([\u3000\xa0\s\t]+\x24)/g,"");if(a){for(var o=i.split("."),s=z.codes,l=0,u;l<o.length-1;)u=o[l++],s[u]||(s[u]={}),s=s[u];u=o[l],s[u]=a}return a})};z.codes={};z.source=function(e){for(var t=e.split("."),r=z.codes,i=0;r&&i<t.length;){var n=t[i++];r=r[n]}return typeof r!="string"?(console.error('Shader "'+e+'" not existed in library'),""):r};const ua=`@export clay.prez.vertex
uniform mat4 WVP : WORLDVIEWPROJECTION;
attribute vec3 pos : POSITION;
attribute vec2 uv : TEXCOORD_0;
uniform vec2 uvRepeat : [1.0, 1.0];
uniform vec2 uvOffset : [0.0, 0.0];
@import clay.chunk.skinning_header
@import clay.chunk.instancing_header
varying vec2 v_Texcoord;
void main()
{
 vec4 P = vec4(pos, 1.0);
#ifdef SKINNING
 @import clay.chunk.skin_matrix
 P = skinMatrixWS * P;
#endif
#ifdef INSTANCING
 @import clay.chunk.instancing_matrix
 P = instanceMat * P;
#endif
 gl_Position = WVP * P;
 v_Texcoord = uv * uvRepeat + uvOffset;
}
@end
@export clay.prez.fragment
uniform sampler2D alphaMap;
uniform float alphaCutoff: 0.0;
varying vec2 v_Texcoord;
void main()
{
 if (alphaCutoff > 0.0) {
 if (texture2D(alphaMap, v_Texcoord).a <= alphaCutoff) {
 discard;
 }
 }
 gl_FragColor = vec4(0.0,0.0,0.0,1.0);
}
@end`;var D={};D.create=function(){var e=new Se(16);return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=1,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=1,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,e};D.clone=function(e){var t=new Se(16);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t[4]=e[4],t[5]=e[5],t[6]=e[6],t[7]=e[7],t[8]=e[8],t[9]=e[9],t[10]=e[10],t[11]=e[11],t[12]=e[12],t[13]=e[13],t[14]=e[14],t[15]=e[15],t};D.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4],e[5]=t[5],e[6]=t[6],e[7]=t[7],e[8]=t[8],e[9]=t[9],e[10]=t[10],e[11]=t[11],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15],e};D.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=1,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=1,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,e};D.transpose=function(e,t){if(e===t){var r=t[1],i=t[2],n=t[3],a=t[6],o=t[7],s=t[11];e[1]=t[4],e[2]=t[8],e[3]=t[12],e[4]=r,e[6]=t[9],e[7]=t[13],e[8]=i,e[9]=a,e[11]=t[14],e[12]=n,e[13]=o,e[14]=s}else e[0]=t[0],e[1]=t[4],e[2]=t[8],e[3]=t[12],e[4]=t[1],e[5]=t[5],e[6]=t[9],e[7]=t[13],e[8]=t[2],e[9]=t[6],e[10]=t[10],e[11]=t[14],e[12]=t[3],e[13]=t[7],e[14]=t[11],e[15]=t[15];return e};D.invert=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=t[4],s=t[5],l=t[6],u=t[7],f=t[8],h=t[9],d=t[10],c=t[11],v=t[12],p=t[13],m=t[14],_=t[15],x=r*s-i*o,T=r*l-n*o,g=r*u-a*o,E=i*l-n*s,S=i*u-a*s,C=n*u-a*l,A=f*p-h*v,N=f*m-d*v,H=f*_-c*v,R=h*m-d*p,U=h*_-c*p,V=d*_-c*m,I=x*V-T*U+g*R+E*H-S*N+C*A;return I?(I=1/I,e[0]=(s*V-l*U+u*R)*I,e[1]=(n*U-i*V-a*R)*I,e[2]=(p*C-m*S+_*E)*I,e[3]=(d*S-h*C-c*E)*I,e[4]=(l*H-o*V-u*N)*I,e[5]=(r*V-n*H+a*N)*I,e[6]=(m*g-v*C-_*T)*I,e[7]=(f*C-d*g+c*T)*I,e[8]=(o*U-s*H+u*A)*I,e[9]=(i*H-r*U-a*A)*I,e[10]=(v*S-p*g+_*x)*I,e[11]=(h*g-f*S-c*x)*I,e[12]=(s*N-o*R-l*A)*I,e[13]=(r*R-i*N+n*A)*I,e[14]=(p*T-v*E-m*x)*I,e[15]=(f*E-h*T+d*x)*I,e):null};D.adjoint=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=t[4],s=t[5],l=t[6],u=t[7],f=t[8],h=t[9],d=t[10],c=t[11],v=t[12],p=t[13],m=t[14],_=t[15];return e[0]=s*(d*_-c*m)-h*(l*_-u*m)+p*(l*c-u*d),e[1]=-(i*(d*_-c*m)-h*(n*_-a*m)+p*(n*c-a*d)),e[2]=i*(l*_-u*m)-s*(n*_-a*m)+p*(n*u-a*l),e[3]=-(i*(l*c-u*d)-s*(n*c-a*d)+h*(n*u-a*l)),e[4]=-(o*(d*_-c*m)-f*(l*_-u*m)+v*(l*c-u*d)),e[5]=r*(d*_-c*m)-f*(n*_-a*m)+v*(n*c-a*d),e[6]=-(r*(l*_-u*m)-o*(n*_-a*m)+v*(n*u-a*l)),e[7]=r*(l*c-u*d)-o*(n*c-a*d)+f*(n*u-a*l),e[8]=o*(h*_-c*p)-f*(s*_-u*p)+v*(s*c-u*h),e[9]=-(r*(h*_-c*p)-f*(i*_-a*p)+v*(i*c-a*h)),e[10]=r*(s*_-u*p)-o*(i*_-a*p)+v*(i*u-a*s),e[11]=-(r*(s*c-u*h)-o*(i*c-a*h)+f*(i*u-a*s)),e[12]=-(o*(h*m-d*p)-f*(s*m-l*p)+v*(s*d-l*h)),e[13]=r*(h*m-d*p)-f*(i*m-n*p)+v*(i*d-n*h),e[14]=-(r*(s*m-l*p)-o*(i*m-n*p)+v*(i*l-n*s)),e[15]=r*(s*d-l*h)-o*(i*d-n*h)+f*(i*l-n*s),e};D.determinant=function(e){var t=e[0],r=e[1],i=e[2],n=e[3],a=e[4],o=e[5],s=e[6],l=e[7],u=e[8],f=e[9],h=e[10],d=e[11],c=e[12],v=e[13],p=e[14],m=e[15],_=t*o-r*a,x=t*s-i*a,T=t*l-n*a,g=r*s-i*o,E=r*l-n*o,S=i*l-n*s,C=u*v-f*c,A=u*p-h*c,N=u*m-d*c,H=f*p-h*v,R=f*m-d*v,U=h*m-d*p;return _*U-x*R+T*H+g*N-E*A+S*C};D.multiply=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=t[6],f=t[7],h=t[8],d=t[9],c=t[10],v=t[11],p=t[12],m=t[13],_=t[14],x=t[15],T=r[0],g=r[1],E=r[2],S=r[3];return e[0]=T*i+g*s+E*h+S*p,e[1]=T*n+g*l+E*d+S*m,e[2]=T*a+g*u+E*c+S*_,e[3]=T*o+g*f+E*v+S*x,T=r[4],g=r[5],E=r[6],S=r[7],e[4]=T*i+g*s+E*h+S*p,e[5]=T*n+g*l+E*d+S*m,e[6]=T*a+g*u+E*c+S*_,e[7]=T*o+g*f+E*v+S*x,T=r[8],g=r[9],E=r[10],S=r[11],e[8]=T*i+g*s+E*h+S*p,e[9]=T*n+g*l+E*d+S*m,e[10]=T*a+g*u+E*c+S*_,e[11]=T*o+g*f+E*v+S*x,T=r[12],g=r[13],E=r[14],S=r[15],e[12]=T*i+g*s+E*h+S*p,e[13]=T*n+g*l+E*d+S*m,e[14]=T*a+g*u+E*c+S*_,e[15]=T*o+g*f+E*v+S*x,e};D.multiplyAffine=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[4],s=t[5],l=t[6],u=t[8],f=t[9],h=t[10],d=t[12],c=t[13],v=t[14],p=r[0],m=r[1],_=r[2];return e[0]=p*i+m*o+_*u,e[1]=p*n+m*s+_*f,e[2]=p*a+m*l+_*h,p=r[4],m=r[5],_=r[6],e[4]=p*i+m*o+_*u,e[5]=p*n+m*s+_*f,e[6]=p*a+m*l+_*h,p=r[8],m=r[9],_=r[10],e[8]=p*i+m*o+_*u,e[9]=p*n+m*s+_*f,e[10]=p*a+m*l+_*h,p=r[12],m=r[13],_=r[14],e[12]=p*i+m*o+_*u+d,e[13]=p*n+m*s+_*f+c,e[14]=p*a+m*l+_*h+v,e};D.mul=D.multiply;D.mulAffine=D.multiplyAffine;D.translate=function(e,t,r){var i=r[0],n=r[1],a=r[2],o,s,l,u,f,h,d,c,v,p,m,_;return t===e?(e[12]=t[0]*i+t[4]*n+t[8]*a+t[12],e[13]=t[1]*i+t[5]*n+t[9]*a+t[13],e[14]=t[2]*i+t[6]*n+t[10]*a+t[14],e[15]=t[3]*i+t[7]*n+t[11]*a+t[15]):(o=t[0],s=t[1],l=t[2],u=t[3],f=t[4],h=t[5],d=t[6],c=t[7],v=t[8],p=t[9],m=t[10],_=t[11],e[0]=o,e[1]=s,e[2]=l,e[3]=u,e[4]=f,e[5]=h,e[6]=d,e[7]=c,e[8]=v,e[9]=p,e[10]=m,e[11]=_,e[12]=o*i+f*n+v*a+t[12],e[13]=s*i+h*n+p*a+t[13],e[14]=l*i+d*n+m*a+t[14],e[15]=u*i+c*n+_*a+t[15]),e};D.scale=function(e,t,r){var i=r[0],n=r[1],a=r[2];return e[0]=t[0]*i,e[1]=t[1]*i,e[2]=t[2]*i,e[3]=t[3]*i,e[4]=t[4]*n,e[5]=t[5]*n,e[6]=t[6]*n,e[7]=t[7]*n,e[8]=t[8]*a,e[9]=t[9]*a,e[10]=t[10]*a,e[11]=t[11]*a,e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15],e};D.rotate=function(e,t,r,i){var n=i[0],a=i[1],o=i[2],s=Math.sqrt(n*n+a*a+o*o),l,u,f,h,d,c,v,p,m,_,x,T,g,E,S,C,A,N,H,R,U,V,I,G;return Math.abs(s)<Cr?null:(s=1/s,n*=s,a*=s,o*=s,l=Math.sin(r),u=Math.cos(r),f=1-u,h=t[0],d=t[1],c=t[2],v=t[3],p=t[4],m=t[5],_=t[6],x=t[7],T=t[8],g=t[9],E=t[10],S=t[11],C=n*n*f+u,A=a*n*f+o*l,N=o*n*f-a*l,H=n*a*f-o*l,R=a*a*f+u,U=o*a*f+n*l,V=n*o*f+a*l,I=a*o*f-n*l,G=o*o*f+u,e[0]=h*C+p*A+T*N,e[1]=d*C+m*A+g*N,e[2]=c*C+_*A+E*N,e[3]=v*C+x*A+S*N,e[4]=h*H+p*R+T*U,e[5]=d*H+m*R+g*U,e[6]=c*H+_*R+E*U,e[7]=v*H+x*R+S*U,e[8]=h*V+p*I+T*G,e[9]=d*V+m*I+g*G,e[10]=c*V+_*I+E*G,e[11]=v*V+x*I+S*G,t!==e&&(e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e)};D.rotateX=function(e,t,r){var i=Math.sin(r),n=Math.cos(r),a=t[4],o=t[5],s=t[6],l=t[7],u=t[8],f=t[9],h=t[10],d=t[11];return t!==e&&(e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e[4]=a*n+u*i,e[5]=o*n+f*i,e[6]=s*n+h*i,e[7]=l*n+d*i,e[8]=u*n-a*i,e[9]=f*n-o*i,e[10]=h*n-s*i,e[11]=d*n-l*i,e};D.rotateY=function(e,t,r){var i=Math.sin(r),n=Math.cos(r),a=t[0],o=t[1],s=t[2],l=t[3],u=t[8],f=t[9],h=t[10],d=t[11];return t!==e&&(e[4]=t[4],e[5]=t[5],e[6]=t[6],e[7]=t[7],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e[0]=a*n-u*i,e[1]=o*n-f*i,e[2]=s*n-h*i,e[3]=l*n-d*i,e[8]=a*i+u*n,e[9]=o*i+f*n,e[10]=s*i+h*n,e[11]=l*i+d*n,e};D.rotateZ=function(e,t,r){var i=Math.sin(r),n=Math.cos(r),a=t[0],o=t[1],s=t[2],l=t[3],u=t[4],f=t[5],h=t[6],d=t[7];return t!==e&&(e[8]=t[8],e[9]=t[9],e[10]=t[10],e[11]=t[11],e[12]=t[12],e[13]=t[13],e[14]=t[14],e[15]=t[15]),e[0]=a*n+u*i,e[1]=o*n+f*i,e[2]=s*n+h*i,e[3]=l*n+d*i,e[4]=u*n-a*i,e[5]=f*n-o*i,e[6]=h*n-s*i,e[7]=d*n-l*i,e};D.fromRotationTranslation=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=i+i,l=n+n,u=a+a,f=i*s,h=i*l,d=i*u,c=n*l,v=n*u,p=a*u,m=o*s,_=o*l,x=o*u;return e[0]=1-(c+p),e[1]=h+x,e[2]=d-_,e[3]=0,e[4]=h-x,e[5]=1-(f+p),e[6]=v+m,e[7]=0,e[8]=d+_,e[9]=v-m,e[10]=1-(f+c),e[11]=0,e[12]=r[0],e[13]=r[1],e[14]=r[2],e[15]=1,e};D.fromQuat=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=r+r,s=i+i,l=n+n,u=r*o,f=i*o,h=i*s,d=n*o,c=n*s,v=n*l,p=a*o,m=a*s,_=a*l;return e[0]=1-h-v,e[1]=f+_,e[2]=d-m,e[3]=0,e[4]=f-_,e[5]=1-u-v,e[6]=c+p,e[7]=0,e[8]=d+m,e[9]=c-p,e[10]=1-u-h,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,e};D.frustum=function(e,t,r,i,n,a,o){var s=1/(r-t),l=1/(n-i),u=1/(a-o);return e[0]=a*2*s,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=a*2*l,e[6]=0,e[7]=0,e[8]=(r+t)*s,e[9]=(n+i)*l,e[10]=(o+a)*u,e[11]=-1,e[12]=0,e[13]=0,e[14]=o*a*2*u,e[15]=0,e};D.perspective=function(e,t,r,i,n){var a=1/Math.tan(t/2),o=1/(i-n);return e[0]=a/r,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=a,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=(n+i)*o,e[11]=-1,e[12]=0,e[13]=0,e[14]=2*n*i*o,e[15]=0,e};D.ortho=function(e,t,r,i,n,a,o){var s=1/(t-r),l=1/(i-n),u=1/(a-o);return e[0]=-2*s,e[1]=0,e[2]=0,e[3]=0,e[4]=0,e[5]=-2*l,e[6]=0,e[7]=0,e[8]=0,e[9]=0,e[10]=2*u,e[11]=0,e[12]=(t+r)*s,e[13]=(n+i)*l,e[14]=(o+a)*u,e[15]=1,e};D.lookAt=function(e,t,r,i){var n,a,o,s,l,u,f,h,d,c,v=t[0],p=t[1],m=t[2],_=i[0],x=i[1],T=i[2],g=r[0],E=r[1],S=r[2];return Math.abs(v-g)<Cr&&Math.abs(p-E)<Cr&&Math.abs(m-S)<Cr?D.identity(e):(f=v-g,h=p-E,d=m-S,c=1/Math.sqrt(f*f+h*h+d*d),f*=c,h*=c,d*=c,n=x*d-T*h,a=T*f-_*d,o=_*h-x*f,c=Math.sqrt(n*n+a*a+o*o),c?(c=1/c,n*=c,a*=c,o*=c):(n=0,a=0,o=0),s=h*o-d*a,l=d*n-f*o,u=f*a-h*n,c=Math.sqrt(s*s+l*l+u*u),c?(c=1/c,s*=c,l*=c,u*=c):(s=0,l=0,u=0),e[0]=n,e[1]=s,e[2]=f,e[3]=0,e[4]=a,e[5]=l,e[6]=h,e[7]=0,e[8]=o,e[9]=u,e[10]=d,e[11]=0,e[12]=-(n*v+a*p+o*m),e[13]=-(s*v+l*p+u*m),e[14]=-(f*v+h*p+d*m),e[15]=1,e)};D.frob=function(e){return Math.sqrt(Math.pow(e[0],2)+Math.pow(e[1],2)+Math.pow(e[2],2)+Math.pow(e[3],2)+Math.pow(e[4],2)+Math.pow(e[5],2)+Math.pow(e[6],2)+Math.pow(e[7],2)+Math.pow(e[8],2)+Math.pow(e[9],2)+Math.pow(e[10],2)+Math.pow(e[11],2)+Math.pow(e[12],2)+Math.pow(e[13],2)+Math.pow(e[14],2)+Math.pow(e[15],2))};var y={};y.create=function(){var e=new Se(3);return e[0]=0,e[1]=0,e[2]=0,e};y.clone=function(e){var t=new Se(3);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t};y.fromValues=function(e,t,r){var i=new Se(3);return i[0]=e,i[1]=t,i[2]=r,i};y.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e};y.set=function(e,t,r,i){return e[0]=t,e[1]=r,e[2]=i,e};y.add=function(e,t,r){return e[0]=t[0]+r[0],e[1]=t[1]+r[1],e[2]=t[2]+r[2],e};y.subtract=function(e,t,r){return e[0]=t[0]-r[0],e[1]=t[1]-r[1],e[2]=t[2]-r[2],e};y.sub=y.subtract;y.multiply=function(e,t,r){return e[0]=t[0]*r[0],e[1]=t[1]*r[1],e[2]=t[2]*r[2],e};y.mul=y.multiply;y.divide=function(e,t,r){return e[0]=t[0]/r[0],e[1]=t[1]/r[1],e[2]=t[2]/r[2],e};y.div=y.divide;y.min=function(e,t,r){return e[0]=Math.min(t[0],r[0]),e[1]=Math.min(t[1],r[1]),e[2]=Math.min(t[2],r[2]),e};y.max=function(e,t,r){return e[0]=Math.max(t[0],r[0]),e[1]=Math.max(t[1],r[1]),e[2]=Math.max(t[2],r[2]),e};y.scale=function(e,t,r){return e[0]=t[0]*r,e[1]=t[1]*r,e[2]=t[2]*r,e};y.scaleAndAdd=function(e,t,r,i){return e[0]=t[0]+r[0]*i,e[1]=t[1]+r[1]*i,e[2]=t[2]+r[2]*i,e};y.distance=function(e,t){var r=t[0]-e[0],i=t[1]-e[1],n=t[2]-e[2];return Math.sqrt(r*r+i*i+n*n)};y.dist=y.distance;y.squaredDistance=function(e,t){var r=t[0]-e[0],i=t[1]-e[1],n=t[2]-e[2];return r*r+i*i+n*n};y.sqrDist=y.squaredDistance;y.length=function(e){var t=e[0],r=e[1],i=e[2];return Math.sqrt(t*t+r*r+i*i)};y.len=y.length;y.squaredLength=function(e){var t=e[0],r=e[1],i=e[2];return t*t+r*r+i*i};y.sqrLen=y.squaredLength;y.negate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e[2]=-t[2],e};y.inverse=function(e,t){return e[0]=1/t[0],e[1]=1/t[1],e[2]=1/t[2],e};y.normalize=function(e,t){var r=t[0],i=t[1],n=t[2],a=r*r+i*i+n*n;return a>0&&(a=1/Math.sqrt(a),e[0]=t[0]*a,e[1]=t[1]*a,e[2]=t[2]*a),e};y.dot=function(e,t){return e[0]*t[0]+e[1]*t[1]+e[2]*t[2]};y.cross=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=r[0],s=r[1],l=r[2];return e[0]=n*l-a*s,e[1]=a*o-i*l,e[2]=i*s-n*o,e};y.lerp=function(e,t,r,i){var n=t[0],a=t[1],o=t[2];return e[0]=n+i*(r[0]-n),e[1]=a+i*(r[1]-a),e[2]=o+i*(r[2]-o),e};y.random=function(e,t){t=t||1;var r=Ut()*2*Math.PI,i=Ut()*2-1,n=Math.sqrt(1-i*i)*t;return e[0]=Math.cos(r)*n,e[1]=Math.sin(r)*n,e[2]=i*t,e};y.transformMat4=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=r[3]*i+r[7]*n+r[11]*a+r[15];return o=o||1,e[0]=(r[0]*i+r[4]*n+r[8]*a+r[12])/o,e[1]=(r[1]*i+r[5]*n+r[9]*a+r[13])/o,e[2]=(r[2]*i+r[6]*n+r[10]*a+r[14])/o,e};y.transformMat3=function(e,t,r){var i=t[0],n=t[1],a=t[2];return e[0]=i*r[0]+n*r[3]+a*r[6],e[1]=i*r[1]+n*r[4]+a*r[7],e[2]=i*r[2]+n*r[5]+a*r[8],e};y.transformQuat=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=r[0],s=r[1],l=r[2],u=r[3],f=u*i+s*a-l*n,h=u*n+l*i-o*a,d=u*a+o*n-s*i,c=-o*i-s*n-l*a;return e[0]=f*u+c*-o+h*-l-d*-s,e[1]=h*u+c*-s+d*-o-f*-l,e[2]=d*u+c*-l+f*-s-h*-o,e};y.rotateX=function(e,t,r,i){var n=[],a=[];return n[0]=t[0]-r[0],n[1]=t[1]-r[1],n[2]=t[2]-r[2],a[0]=n[0],a[1]=n[1]*Math.cos(i)-n[2]*Math.sin(i),a[2]=n[1]*Math.sin(i)+n[2]*Math.cos(i),e[0]=a[0]+r[0],e[1]=a[1]+r[1],e[2]=a[2]+r[2],e};y.rotateY=function(e,t,r,i){var n=[],a=[];return n[0]=t[0]-r[0],n[1]=t[1]-r[1],n[2]=t[2]-r[2],a[0]=n[2]*Math.sin(i)+n[0]*Math.cos(i),a[1]=n[1],a[2]=n[2]*Math.cos(i)-n[0]*Math.sin(i),e[0]=a[0]+r[0],e[1]=a[1]+r[1],e[2]=a[2]+r[2],e};y.rotateZ=function(e,t,r,i){var n=[],a=[];return n[0]=t[0]-r[0],n[1]=t[1]-r[1],n[2]=t[2]-r[2],a[0]=n[0]*Math.cos(i)-n[1]*Math.sin(i),a[1]=n[0]*Math.sin(i)+n[1]*Math.cos(i),a[2]=n[2],e[0]=a[0]+r[0],e[1]=a[1]+r[1],e[2]=a[2]+r[2],e};y.forEach=(function(){var e=y.create();return function(t,r,i,n,a,o){var s,l;for(r||(r=3),i||(i=0),n?l=Math.min(n*r+i,t.length):l=t.length,s=i;s<l;s+=r)e[0]=t[s],e[1]=t[s+1],e[2]=t[s+2],a(e,e,o),t[s]=e[0],t[s+1]=e[1],t[s+2]=e[2];return t}})();y.angle=function(e,t){var r=y.fromValues(e[0],e[1],e[2]),i=y.fromValues(t[0],t[1],t[2]);y.normalize(r,r),y.normalize(i,i);var n=y.dot(r,i);return n>1?0:Math.acos(n)};z.import(ua);var ae=D.create,fn={};function hn(e){return e.material}function Wo(e,t,r){return t.uniforms[r].value}function Xo(e,t,r,i){return r!==i}function qo(e){return!0}function cn(){}var dn={float:L.FLOAT,byte:L.BYTE,ubyte:L.UNSIGNED_BYTE,short:L.SHORT,ushort:L.UNSIGNED_SHORT};function jo(e,t,r){this.availableAttributes=e,this.availableAttributeSymbols=t,this.indicesBuffer=r,this.vao=null}function Zo(e){var t,r;this.bind=function(i){t||(t=Q.createCanvas(),t.width=t.height=1,t.getContext("2d"));var n=i.gl,a=!r;a&&(r=n.createTexture()),n.bindTexture(n.TEXTURE_2D,r),a&&n.texImage2D(n.TEXTURE_2D,0,n.RGBA,n.RGBA,n.UNSIGNED_BYTE,t)},this.unbind=function(i){i.gl.bindTexture(i.gl.TEXTURE_2D,null)},this.isRenderable=function(){return!0}}var Ve=be.extend(function(){return{canvas:null,_width:100,_height:100,devicePixelRatio:typeof window<"u"&&window.devicePixelRatio||1,clearColor:[0,0,0,0],clearBit:17664,alpha:!0,depth:!0,stencil:!1,antialias:!0,premultipliedAlpha:!0,preserveDrawingBuffer:!1,throwError:!0,gl:null,viewport:{},maxJointNumber:20,__currentFrameBuffer:null,_viewportStack:[],_clearStack:[],_sceneRendering:null}},function(){this.canvas||(this.canvas=Q.createCanvas());var e=this.canvas;try{var t={alpha:this.alpha,depth:this.depth,stencil:this.stencil,antialias:this.antialias,premultipliedAlpha:this.premultipliedAlpha,preserveDrawingBuffer:this.preserveDrawingBuffer};if(this.gl=e.getContext("webgl",t)||e.getContext("experimental-webgl",t),!this.gl)throw new Error;this._glinfo=new Ao(this.gl),this.gl.targetRenderer&&console.error("Already created a renderer"),this.gl.targetRenderer=this,this.resize()}catch(r){throw"Error creating WebGL Context "+r}this._programMgr=new aa(this),this._placeholderTexture=new Zo},{resize:function(e,t){var r=this.canvas,i=this.devicePixelRatio;e!=null?(r.style&&(r.style.width=e+"px",r.style.height=t+"px"),r.width=e*i,r.height=t*i,this._width=e,this._height=t):(this._width=r.width/i,this._height=r.height/i),this.setViewport(0,0,this._width,this._height)},getWidth:function(){return this._width},getHeight:function(){return this._height},getViewportAspect:function(){var e=this.viewport;return e.width/e.height},setDevicePixelRatio:function(e){this.devicePixelRatio=e,this.resize(this._width,this._height)},getDevicePixelRatio:function(){return this.devicePixelRatio},getGLExtension:function(e){return this._glinfo.getExtension(e)},getGLParameter:function(e){return this._glinfo.getParameter(e)},setViewport:function(e,t,r,i,n){if(typeof e=="object"){var a=e;e=a.x,t=a.y,r=a.width,i=a.height,n=a.devicePixelRatio}n=n||this.devicePixelRatio,this.gl.viewport(e*n,t*n,r*n,i*n),this.viewport={x:e,y:t,width:r,height:i,devicePixelRatio:n}},saveViewport:function(){this._viewportStack.push(this.viewport)},restoreViewport:function(){this._viewportStack.length>0&&this.setViewport(this._viewportStack.pop())},saveClear:function(){this._clearStack.push({clearBit:this.clearBit,clearColor:this.clearColor})},restoreClear:function(){if(this._clearStack.length>0){var e=this._clearStack.pop();this.clearColor=e.clearColor,this.clearBit=e.clearBit}},bindSceneRendering:function(e){this._sceneRendering=e},render:function(e,t,r,i){var n=this.gl,a=this.clearColor;if(this.clearBit){n.colorMask(!0,!0,!0,!0),n.depthMask(!0);var o=this.viewport,s=!1,l=o.devicePixelRatio;(o.width!==this._width||o.height!==this._height||l&&l!==this.devicePixelRatio||o.x||o.y)&&(s=!0,n.enable(n.SCISSOR_TEST),n.scissor(o.x*l,o.y*l,o.width*l,o.height*l)),n.clearColor(a[0],a[1],a[2],a[3]),n.clear(this.clearBit),s&&n.disable(n.SCISSOR_TEST)}if(r||e.update(!1),e.updateLights(),t=t||e.getMainCamera(),!t){console.error("Can't find camera in the scene.");return}t.update();var u=e.updateRenderList(t,!0);this._sceneRendering=e;var f=u.opaque,h=u.transparent,d=e.material;e.trigger("beforerender",this,e,t,u),i?(this.renderPreZ(f,e,t),n.depthFunc(n.LEQUAL)):n.depthFunc(n.LESS);for(var c=ae(),v=y.create(),p=0;p<h.length;p++){var m=h[p];D.multiplyAffine(c,t.viewMatrix.array,m.worldTransform.array),y.transformMat4(v,m.position.array,c),m.__depth=v[2]}this.renderPass(f,t,{getMaterial:function(_){return d||_.material},sortCompare:this.opaqueSortCompare}),this.renderPass(h,t,{getMaterial:function(_){return d||_.material},sortCompare:this.transparentSortCompare}),e.trigger("afterrender",this,e,t,u),this._sceneRendering=null},getProgram:function(e,t,r){return t=t||e.material,this._programMgr.getProgram(e,t,r)},validateProgram:function(e){if(e.__error){var t=e.__error;if(fn[e.__uid__])return;if(fn[e.__uid__]=!0,this.throwError)throw new Error(t);this.trigger("error",t)}},updatePrograms:function(e,t,r){var i=r&&r.getMaterial||hn;t=t||null;for(var n=0;n<e.length;n++){var a=e[n],o=i.call(this,a);if(n>0){var s=e[n-1],l=s.joints?s.joints.length:0,u=a.joints?a.joints.length:0;if(u===l&&a.material===s.material&&a.lightGroup===s.lightGroup){a.__program=s.__program;continue}}var f=this._programMgr.getProgram(a,o,t);this.validateProgram(f),a.__program=f}},renderPass:function(e,t,r){this.trigger("beforerenderpass",this,e,t,r),r=r||{},r.getMaterial=r.getMaterial||hn,r.getUniform=r.getUniform||Wo,r.isMaterialChanged=r.isMaterialChanged||Xo,r.beforeRender=r.beforeRender||cn,r.afterRender=r.afterRender||cn;var i=r.ifRender||qo;this.updatePrograms(e,this._sceneRendering,r),r.sortCompare&&e.sort(r.sortCompare);var n=this.viewport,a=n.devicePixelRatio,o=[n.x*a,n.y*a,n.width*a,n.height*a],s=this.devicePixelRatio,l=this.__currentFrameBuffer?[this.__currentFrameBuffer.getTextureWidth(),this.__currentFrameBuffer.getTextureHeight()]:[this._width*s,this._height*s],u=[o[2],o[3]],f=Date.now();t?(D.copy(ne.VIEW,t.viewMatrix.array),D.copy(ne.PROJECTION,t.projectionMatrix.array),D.copy(ne.VIEWINVERSE,t.worldTransform.array)):(D.identity(ne.VIEW),D.identity(ne.PROJECTION),D.identity(ne.VIEWINVERSE)),D.multiply(ne.VIEWPROJECTION,ne.PROJECTION,ne.VIEW),D.invert(ne.PROJECTIONINVERSE,ne.PROJECTION),D.invert(ne.VIEWPROJECTIONINVERSE,ne.VIEWPROJECTION);for(var h=this.gl,d=this._sceneRendering,c,v,p,m,_,x,T,g,E,S,C,A,N=null,H=0;H<e.length;H++){var R=e[H],U=R.worldTransform!=null,V;if(i(R)){U&&(V=R.isSkinnedMesh&&R.isSkinnedMesh()?R.offsetMatrix?R.offsetMatrix.array:ne.IDENTITY:R.worldTransform.array);var I=R.geometry,G=r.getMaterial.call(this,R),X=R.__program,q=G.shader,ie=I.__uid__+"-"+X.__uid__,_e=ie!==S;S=ie,U&&(D.copy(ne.WORLD,V),D.multiply(ne.WORLDVIEWPROJECTION,ne.VIEWPROJECTION,V),D.multiplyAffine(ne.WORLDVIEW,ne.VIEW,V),(q.matrixSemantics.WORLDINVERSE||q.matrixSemantics.WORLDINVERSETRANSPOSE)&&D.invert(ne.WORLDINVERSE,V),(q.matrixSemantics.WORLDVIEWINVERSE||q.matrixSemantics.WORLDVIEWINVERSETRANSPOSE)&&D.invert(ne.WORLDVIEWINVERSE,ne.WORLDVIEW),(q.matrixSemantics.WORLDVIEWPROJECTIONINVERSE||q.matrixSemantics.WORLDVIEWPROJECTIONINVERSETRANSPOSE)&&D.invert(ne.WORLDVIEWPROJECTIONINVERSE,ne.WORLDVIEWPROJECTION)),R.beforeRender&&R.beforeRender(this),r.beforeRender.call(this,R,G,c);var we=X!==v;we?(X.bind(this),X.setUniformOfSemantic(h,"VIEWPORT",o),X.setUniformOfSemantic(h,"WINDOW_SIZE",l),t&&(X.setUniformOfSemantic(h,"NEAR",t.near),X.setUniformOfSemantic(h,"FAR",t.far)),X.setUniformOfSemantic(h,"DEVICEPIXELRATIO",a),X.setUniformOfSemantic(h,"TIME",f),X.setUniformOfSemantic(h,"VIEWPORT_SIZE",u),d&&d.setLightUniforms(X,R.lightGroup,this)):X=v,(we||r.isMaterialChanged(R,p,G,c))&&(G.depthTest!==m&&(G.depthTest?h.enable(h.DEPTH_TEST):h.disable(h.DEPTH_TEST),m=G.depthTest),G.depthMask!==_&&(h.depthMask(G.depthMask),_=G.depthMask),G.transparent!==E&&(G.transparent?h.enable(h.BLEND):h.disable(h.BLEND),E=G.transparent),G.transparent&&(G.blend?G.blend(h):(h.blendEquationSeparate(h.FUNC_ADD,h.FUNC_ADD),h.blendFuncSeparate(h.SRC_ALPHA,h.ONE_MINUS_SRC_ALPHA,h.ONE,h.ONE_MINUS_SRC_ALPHA))),A=this._bindMaterial(R,G,X,p||null,c||null,v||null,r.getUniform),c=G);var ce=q.matrixSemanticKeys;if(U)for(var xe=0;xe<ce.length;xe++){var de=ce[xe],Ae=q.matrixSemantics[de],Be=ne[de];if(Ae.isTranspose){var Oe=ne[Ae.semanticNoTranspose];D.transpose(Be,Oe)}X.setUniform(h,Ae.type,Ae.symbol,Be)}R.cullFace!==T&&(T=R.cullFace,h.cullFace(T)),R.frontFace!==g&&(g=R.frontFace,h.frontFace(g)),R.culling!==x&&(x=R.culling,x?h.enable(h.CULL_FACE):h.disable(h.CULL_FACE)),this._updateSkeleton(R,X,A),_e&&(C=this._bindVAO(N,q,I,X)),this._renderObject(R,C,X),r.afterRender(this,R),R.afterRender&&R.afterRender(this),v=X,p=R}}this.trigger("afterrenderpass",this,e,t,r)},getMaxJointNumber:function(){return this.maxJointNumber},_updateSkeleton:function(e,t,r){var i=this.gl,n=e.skeleton;if(n)if(n.update(),e.joints.length>this.getMaxJointNumber()){var a=n.getSubSkinMatricesTexture(e.__uid__,e.joints);t.useTextureSlot(this,a,r),t.setUniform(i,"1i","skinMatricesTexture",r),t.setUniform(i,"1f","skinMatricesTextureSize",a.width)}else{var o=n.getSubSkinMatrices(e.__uid__,e.joints);t.setUniformOfSemantic(i,"SKIN_MATRIX",o)}},_renderObject:function(e,t,r){var i=this.gl,n=e.geometry,a=e.mode;a==null&&(a=4);var o=null,s=e.isInstancedMesh&&e.isInstancedMesh();if(s&&(o=this.getGLExtension("ANGLE_instanced_arrays"),!o)){console.warn("Device not support ANGLE_instanced_arrays extension");return}var l;if(s&&(l=this._bindInstancedAttributes(e,r,o)),t.indicesBuffer){var u=this.getGLExtension("OES_element_index_uint"),f=u&&n.indices instanceof Uint32Array,h=f?i.UNSIGNED_INT:i.UNSIGNED_SHORT;s?o.drawElementsInstancedANGLE(a,t.indicesBuffer.count,h,0,e.getInstanceCount()):i.drawElements(a,t.indicesBuffer.count,h,0)}else s?o.drawArraysInstancedANGLE(a,0,n.vertexCount,e.getInstanceCount()):i.drawArrays(a,0,n.vertexCount);if(s)for(var d=0;d<l.length;d++)i.disableVertexAttribArray(l[d])},_bindInstancedAttributes:function(e,t,r){for(var i=this.gl,n=e.getInstancedAttributesBuffers(this),a=[],o=0;o<n.length;o++){var s=n[o],l=t.getAttribLocation(i,s.symbol);if(!(l<0)){var u=dn[s.type]||i.FLOAT;i.enableVertexAttribArray(l),i.bindBuffer(i.ARRAY_BUFFER,s.buffer),i.vertexAttribPointer(l,s.size,u,!1,0,0),r.vertexAttribDivisorANGLE(l,s.divisor),a.push(l)}}return a},_bindMaterial:function(e,t,r,i,n,a,o){for(var s=this.gl,l=a===r,u=r.currentTextureSlot(),f=t.getEnabledUniforms(),h=t.getTextureUniforms(),d=this._placeholderTexture,c=0;c<h.length;c++){var v=h[c],p=o(e,t,v),m=t.uniforms[v].type;if(m==="t"&&p)p.__slot=-1;else if(m==="tv")for(var _=0;_<p.length;_++)p[_]&&(p[_].__slot=-1)}d.__slot=-1;for(var c=0;c<f.length;c++){var v=f[c],x=t.uniforms[v],p=o(e,t,v),m=x.type,T=m==="t";if(T&&(!p||!p.isRenderable())&&(p=d),n&&l){var g=o(i,n,v);if(T&&(!g||!g.isRenderable())&&(g=d),g===p){if(T)r.takeCurrentTextureSlot(this,null);else if(m==="tv"&&p)for(var _=0;_<p.length;_++)r.takeCurrentTextureSlot(this,null);continue}}if(p!=null)if(T)if(p.__slot<0){var E=r.currentTextureSlot(),S=r.setUniform(s,"1i",v,E);S&&(r.takeCurrentTextureSlot(this,p),p.__slot=E)}else r.setUniform(s,"1i",v,p.__slot);else if(Array.isArray(p)){if(p.length===0)continue;if(m==="tv"){if(!r.hasUniform(v))continue;for(var C=[],_=0;_<p.length;_++){var A=p[_];if(A.__slot<0){var E=r.currentTextureSlot();C.push(E),r.takeCurrentTextureSlot(this,A),A.__slot=E}else C.push(A.__slot)}r.setUniform(s,"1iv",v,C)}else r.setUniform(s,x.type,v,p)}else r.setUniform(s,x.type,v,p)}var N=r.currentTextureSlot();return r.resetTextureSlot(u),N},_bindVAO:function(e,t,r,i){var n=!r.dynamic,a=this.gl,o=this.__uid__+"-"+i.__uid__,s=r.__vaoCache[o];if(!s){var l=r.getBufferChunks(this);if(!l||!l.length)return;for(var u=l[0],f=u.attributeBuffers,g=u.indicesBuffer,T=[],h=[],d=0;d<f.length;d++){var c=f[d],v=c.name,p=c.semantic,m;if(p){var _=t.attributeSemantics[p];m=_&&_.symbol}else m=v;m&&i.attributes[m]&&(T.push(c),h.push(m))}s=new jo(T,h,g),n&&(r.__vaoCache[o]=s)}var x=!0;e&&n&&(s.vao==null?s.vao=e.createVertexArrayOES():x=!1,e.bindVertexArrayOES(s.vao));var T=s.availableAttributes,g=s.indicesBuffer;if(x){for(var E=i.enableAttributes(this,s.availableAttributeSymbols,e&&n&&s),d=0;d<T.length;d++){var S=E[d];if(S!==-1){var c=T[d],C=c.buffer,A=c.size,N=dn[c.type]||a.FLOAT;a.bindBuffer(a.ARRAY_BUFFER,C),a.vertexAttribPointer(S,A,N,!1,0,0)}}r.isUseIndices()&&a.bindBuffer(a.ELEMENT_ARRAY_BUFFER,g.buffer)}return s},renderPreZ:function(e,t,r){var i=this.gl,n=this._prezMaterial||new at({shader:new z(z.source("clay.prez.vertex"),z.source("clay.prez.fragment"))});this._prezMaterial=n,i.colorMask(!1,!1,!1,!1),i.depthMask(!0),this.renderPass(e,r,{ifRender:function(a){return!a.ignorePreZ},isMaterialChanged:function(a,o){var s=a.material,l=o.material;return s.get("diffuseMap")!==l.get("diffuseMap")||(s.get("alphaCutoff")||0)!==(l.get("alphaCutoff")||0)},getUniform:function(a,o,s){if(s==="alphaMap")return a.material.get("diffuseMap");if(s==="alphaCutoff"){if(a.material.isDefined("fragment","ALPHA_TEST")&&a.material.get("diffuseMap")){var l=a.material.get("alphaCutoff");return l||0}return 0}else return s==="uvRepeat"?a.material.get("uvRepeat"):s==="uvOffset"?a.material.get("uvOffset"):o.get(s)},getMaterial:function(){return n},sort:this.opaqueSortCompare}),i.colorMask(!0,!0,!0,!0),i.depthMask(!0)},disposeScene:function(e){this.disposeNode(e,!0,!0),e.dispose()},disposeNode:function(e,t,r){e.getParent()&&e.getParent().remove(e);var i={};e.traverse(function(n){var a=n.material;if(n.geometry&&t&&n.geometry.dispose(this),r&&a&&!i[a.__uid__]){for(var o=a.getTextureUniforms(),s=0;s<o.length;s++){var l=o[s],u=a.uniforms[l].value,f=a.uniforms[l].type;if(u){if(f==="t")u.dispose&&u.dispose(this);else if(f==="tv")for(var h=0;h<u.length;h++)u[h]&&u[h].dispose&&u[h].dispose(this)}}i[a.__uid__]=!0}n.dispose&&n.dispose(this)},this)},disposeGeometry:function(e){e.dispose(this)},disposeTexture:function(e){e.dispose(this)},disposeFrameBuffer:function(e){e.dispose(this)},dispose:function(){},screenToNDC:function(e,t,r){r||(r=new W),t=this._height-t;var i=this.viewport,n=r.array;return n[0]=(e-i.x)/i.width,n[0]=n[0]*2-1,n[1]=(t-i.y)/i.height,n[1]=n[1]*2-1,r}});Ve.opaqueSortCompare=Ve.prototype.opaqueSortCompare=function(e,t){return e.renderOrder===t.renderOrder?e.__program===t.__program?e.material===t.material?e.geometry.__uid__-t.geometry.__uid__:e.material.__uid__-t.material.__uid__:e.__program&&t.__program?e.__program.__uid__-t.__program.__uid__:0:e.renderOrder-t.renderOrder};Ve.transparentSortCompare=Ve.prototype.transparentSortCompare=function(e,t){return e.renderOrder===t.renderOrder?e.__depth===t.__depth?e.__program===t.__program?e.material===t.material?e.geometry.__uid__-t.geometry.__uid__:e.material.__uid__-t.material.__uid__:e.__program&&t.__program?e.__program.__uid__-t.__program.__uid__:0:e.__depth-t.__depth:e.renderOrder-t.renderOrder};var ne={IDENTITY:ae(),WORLD:ae(),VIEW:ae(),PROJECTION:ae(),WORLDVIEW:ae(),VIEWPROJECTION:ae(),WORLDVIEWPROJECTION:ae(),WORLDINVERSE:ae(),VIEWINVERSE:ae(),PROJECTIONINVERSE:ae(),WORLDVIEWINVERSE:ae(),VIEWPROJECTIONINVERSE:ae(),WORLDVIEWPROJECTIONINVERSE:ae(),WORLDTRANSPOSE:ae(),VIEWTRANSPOSE:ae(),PROJECTIONTRANSPOSE:ae(),WORLDVIEWTRANSPOSE:ae(),VIEWPROJECTIONTRANSPOSE:ae(),WORLDVIEWPROJECTIONTRANSPOSE:ae(),WORLDINVERSETRANSPOSE:ae(),VIEWINVERSETRANSPOSE:ae(),PROJECTIONINVERSETRANSPOSE:ae(),WORLDVIEWINVERSETRANSPOSE:ae(),VIEWPROJECTIONINVERSETRANSPOSE:ae(),WORLDVIEWPROJECTIONINVERSETRANSPOSE:ae()};Ve.COLOR_BUFFER_BIT=L.COLOR_BUFFER_BIT;Ve.DEPTH_BUFFER_BIT=L.DEPTH_BUFFER_BIT;Ve.STENCIL_BUFFER_BIT=L.STENCIL_BUFFER_BIT;var b=function(e,t,r){e=e||0,t=t||0,r=r||0,this.array=y.fromValues(e,t,r),this._dirty=!0};b.prototype={constructor:b,add:function(e){return y.add(this.array,this.array,e.array),this._dirty=!0,this},set:function(e,t,r){return this.array[0]=e,this.array[1]=t,this.array[2]=r,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this.array[2]=e[2],this._dirty=!0,this},clone:function(){return new b(this.x,this.y,this.z)},copy:function(e){return y.copy(this.array,e.array),this._dirty=!0,this},cross:function(e,t){return y.cross(this.array,e.array,t.array),this._dirty=!0,this},dist:function(e){return y.dist(this.array,e.array)},distance:function(e){return y.distance(this.array,e.array)},div:function(e){return y.div(this.array,this.array,e.array),this._dirty=!0,this},divide:function(e){return y.divide(this.array,this.array,e.array),this._dirty=!0,this},dot:function(e){return y.dot(this.array,e.array)},len:function(){return y.len(this.array)},length:function(){return y.length(this.array)},lerp:function(e,t,r){return y.lerp(this.array,e.array,t.array,r),this._dirty=!0,this},min:function(e){return y.min(this.array,this.array,e.array),this._dirty=!0,this},max:function(e){return y.max(this.array,this.array,e.array),this._dirty=!0,this},mul:function(e){return y.mul(this.array,this.array,e.array),this._dirty=!0,this},multiply:function(e){return y.multiply(this.array,this.array,e.array),this._dirty=!0,this},negate:function(){return y.negate(this.array,this.array),this._dirty=!0,this},normalize:function(){return y.normalize(this.array,this.array),this._dirty=!0,this},random:function(e){return y.random(this.array,e),this._dirty=!0,this},scale:function(e){return y.scale(this.array,this.array,e),this._dirty=!0,this},scaleAndAdd:function(e,t){return y.scaleAndAdd(this.array,this.array,e.array,t),this._dirty=!0,this},sqrDist:function(e){return y.sqrDist(this.array,e.array)},squaredDistance:function(e){return y.squaredDistance(this.array,e.array)},sqrLen:function(){return y.sqrLen(this.array)},squaredLength:function(){return y.squaredLength(this.array)},sub:function(e){return y.sub(this.array,this.array,e.array),this._dirty=!0,this},subtract:function(e){return y.subtract(this.array,this.array,e.array),this._dirty=!0,this},transformMat3:function(e){return y.transformMat3(this.array,this.array,e.array),this._dirty=!0,this},transformMat4:function(e){return y.transformMat4(this.array,this.array,e.array),this._dirty=!0,this},transformQuat:function(e){return y.transformQuat(this.array,this.array,e.array),this._dirty=!0,this},applyProjection:function(e){var t=this.array;if(e=e.array,e[15]===0){var r=-1/t[2];t[0]=e[0]*t[0]*r,t[1]=e[5]*t[1]*r,t[2]=(e[10]*t[2]+e[14])*r}else t[0]=e[0]*t[0]+e[12],t[1]=e[5]*t[1]+e[13],t[2]=e[10]*t[2]+e[14];return this._dirty=!0,this},eulerFromQuat:function(e,t){b.eulerFromQuat(this,e,t)},eulerFromMat3:function(e,t){b.eulerFromMat3(this,e,t)},toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};var mr=Object.defineProperty;if(mr){var $r=b.prototype;mr($r,"x",{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),mr($r,"y",{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}}),mr($r,"z",{get:function(){return this.array[2]},set:function(e){this.array[2]=e,this._dirty=!0}})}b.add=function(e,t,r){return y.add(e.array,t.array,r.array),e._dirty=!0,e};b.set=function(e,t,r,i){y.set(e.array,t,r,i),e._dirty=!0};b.copy=function(e,t){return y.copy(e.array,t.array),e._dirty=!0,e};b.cross=function(e,t,r){return y.cross(e.array,t.array,r.array),e._dirty=!0,e};b.dist=function(e,t){return y.distance(e.array,t.array)};b.distance=b.dist;b.div=function(e,t,r){return y.divide(e.array,t.array,r.array),e._dirty=!0,e};b.divide=b.div;b.dot=function(e,t){return y.dot(e.array,t.array)};b.len=function(e){return y.length(e.array)};b.lerp=function(e,t,r,i){return y.lerp(e.array,t.array,r.array,i),e._dirty=!0,e};b.min=function(e,t,r){return y.min(e.array,t.array,r.array),e._dirty=!0,e};b.max=function(e,t,r){return y.max(e.array,t.array,r.array),e._dirty=!0,e};b.mul=function(e,t,r){return y.multiply(e.array,t.array,r.array),e._dirty=!0,e};b.multiply=b.mul;b.negate=function(e,t){return y.negate(e.array,t.array),e._dirty=!0,e};b.normalize=function(e,t){return y.normalize(e.array,t.array),e._dirty=!0,e};b.random=function(e,t){return y.random(e.array,t),e._dirty=!0,e};b.scale=function(e,t,r){return y.scale(e.array,t.array,r),e._dirty=!0,e};b.scaleAndAdd=function(e,t,r,i){return y.scaleAndAdd(e.array,t.array,r.array,i),e._dirty=!0,e};b.sqrDist=function(e,t){return y.sqrDist(e.array,t.array)};b.squaredDistance=b.sqrDist;b.sqrLen=function(e){return y.sqrLen(e.array)};b.squaredLength=b.sqrLen;b.sub=function(e,t,r){return y.subtract(e.array,t.array,r.array),e._dirty=!0,e};b.subtract=b.sub;b.transformMat3=function(e,t,r){return y.transformMat3(e.array,t.array,r.array),e._dirty=!0,e};b.transformMat4=function(e,t,r){return y.transformMat4(e.array,t.array,r.array),e._dirty=!0,e};b.transformQuat=function(e,t,r){return y.transformQuat(e.array,t.array,r.array),e._dirty=!0,e};function ze(e,t,r){return e<t?t:e>r?r:e}var te=Math.atan2,He=Math.asin,Nt=Math.abs;b.eulerFromQuat=function(e,t,d){e._dirty=!0,t=t.array;var i=e.array,n=t[0],a=t[1],o=t[2],s=t[3],l=n*n,u=a*a,f=o*o,h=s*s,d=(d||"XYZ").toUpperCase();switch(d){case"XYZ":i[0]=te(2*(n*s-a*o),h-l-u+f),i[1]=He(ze(2*(n*o+a*s),-1,1)),i[2]=te(2*(o*s-n*a),h+l-u-f);break;case"YXZ":i[0]=He(ze(2*(n*s-a*o),-1,1)),i[1]=te(2*(n*o+a*s),h-l-u+f),i[2]=te(2*(n*a+o*s),h-l+u-f);break;case"ZXY":i[0]=He(ze(2*(n*s+a*o),-1,1)),i[1]=te(2*(a*s-o*n),h-l-u+f),i[2]=te(2*(o*s-n*a),h-l+u-f);break;case"ZYX":i[0]=te(2*(n*s+o*a),h-l-u+f),i[1]=He(ze(2*(a*s-n*o),-1,1)),i[2]=te(2*(n*a+o*s),h+l-u-f);break;case"YZX":i[0]=te(2*(n*s-o*a),h-l+u-f),i[1]=te(2*(a*s-n*o),h+l-u-f),i[2]=He(ze(2*(n*a+o*s),-1,1));break;case"XZY":i[0]=te(2*(n*s+a*o),h-l+u-f),i[1]=te(2*(n*o+a*s),h+l-u-f),i[2]=He(ze(2*(o*s-n*a),-1,1));break;default:console.warn("Unkown order: "+d)}return e};b.eulerFromMat3=function(e,t,v){var i=t.array,n=i[0],a=i[3],o=i[6],s=i[1],l=i[4],u=i[7],f=i[2],h=i[5],d=i[8],c=e.array,v=(v||"XYZ").toUpperCase();switch(v){case"XYZ":c[1]=He(ze(o,-1,1)),Nt(o)<.99999?(c[0]=te(-u,d),c[2]=te(-a,n)):(c[0]=te(h,l),c[2]=0);break;case"YXZ":c[0]=He(-ze(u,-1,1)),Nt(u)<.99999?(c[1]=te(o,d),c[2]=te(s,l)):(c[1]=te(-f,n),c[2]=0);break;case"ZXY":c[0]=He(ze(h,-1,1)),Nt(h)<.99999?(c[1]=te(-f,d),c[2]=te(-a,l)):(c[1]=0,c[2]=te(s,n));break;case"ZYX":c[1]=He(-ze(f,-1,1)),Nt(f)<.99999?(c[0]=te(h,d),c[2]=te(s,n)):(c[0]=0,c[2]=te(-a,l));break;case"YZX":c[2]=He(ze(s,-1,1)),Nt(s)<.99999?(c[0]=te(-u,l),c[1]=te(-f,n)):(c[0]=0,c[1]=te(o,d));break;case"XZY":c[2]=He(-ze(a,-1,1)),Nt(a)<.99999?(c[0]=te(h,l),c[1]=te(o,n)):(c[0]=te(-u,d),c[1]=0);break;default:console.warn("Unkown order: "+v)}return e._dirty=!0,e};Object.defineProperties(b,{POSITIVE_X:{get:function(){return new b(1,0,0)}},NEGATIVE_X:{get:function(){return new b(-1,0,0)}},POSITIVE_Y:{get:function(){return new b(0,1,0)}},NEGATIVE_Y:{get:function(){return new b(0,-1,0)}},POSITIVE_Z:{get:function(){return new b(0,0,1)}},NEGATIVE_Z:{get:function(){return new b(0,0,-1)}},UP:{get:function(){return new b(0,1,0)}},ZERO:{get:function(){return new b}}});var ei=1e-5,wt=function(e,t){this.origin=e||new b,this.direction=t||new b};wt.prototype={constructor:wt,intersectPlane:function(e,t){var r=e.normal.array,i=e.distance,n=this.origin.array,a=this.direction.array,o=y.dot(r,a);if(o===0)return null;t||(t=new b);var s=(y.dot(r,n)-i)/o;return y.scaleAndAdd(t.array,n,a,-s),t._dirty=!0,t},mirrorAgainstPlane:function(e){var t=y.dot(e.normal.array,this.direction.array);y.scaleAndAdd(this.direction.array,this.direction.array,e.normal.array,-t*2),this.direction._dirty=!0},distanceToPoint:(function(){var e=y.create();return function(t){y.sub(e,t,this.origin.array);var r=y.dot(e,this.direction.array);if(r<0)return y.distance(this.origin.array,t);var i=y.lenSquared(e);return Math.sqrt(i-r*r)}})(),intersectSphere:(function(){var e=y.create();return function(t,r,i){var n=this.origin.array,a=this.direction.array;t=t.array,y.sub(e,t,n);var o=y.dot(e,a),s=y.squaredLength(e),l=s-o*o,u=r*r;if(!(l>u)){var f=Math.sqrt(u-l),h=o-f,d=o+f;return i||(i=new b),h<0?d<0?null:(y.scaleAndAdd(i.array,n,a,d),i):(y.scaleAndAdd(i.array,n,a,h),i)}}})(),intersectBoundingBox:function(e,t){var r=this.direction.array,i=this.origin.array,n=e.min.array,a=e.max.array,o=1/r[0],s=1/r[1],l=1/r[2],u,f,h,d,c,v;if(o>=0?(u=(n[0]-i[0])*o,f=(a[0]-i[0])*o):(f=(n[0]-i[0])*o,u=(a[0]-i[0])*o),s>=0?(h=(n[1]-i[1])*s,d=(a[1]-i[1])*s):(d=(n[1]-i[1])*s,h=(a[1]-i[1])*s),u>d||h>f||((h>u||u!==u)&&(u=h),(d<f||f!==f)&&(f=d),l>=0?(c=(n[2]-i[2])*l,v=(a[2]-i[2])*l):(v=(n[2]-i[2])*l,c=(a[2]-i[2])*l),u>v||c>f)||((c>u||u!==u)&&(u=c),(v<f||f!==f)&&(f=v),f<0))return null;var p=u>=0?u:f;return t||(t=new b),y.scaleAndAdd(t.array,i,r,p),t},intersectTriangle:(function(){var e=y.create(),t=y.create(),r=y.create(),i=y.create();return function(n,a,o,s,l,u){var f=this.direction.array,h=this.origin.array;n=n.array,a=a.array,o=o.array,y.sub(e,a,n),y.sub(t,o,n),y.cross(i,t,f);var d=y.dot(e,i);if(s){if(d>-ei)return null}else if(d>-ei&&d<ei)return null;y.sub(r,h,n);var c=y.dot(i,r)/d;if(c<0||c>1)return null;y.cross(i,e,r);var v=y.dot(f,i)/d;if(v<0||v>1||c+v>1)return null;y.cross(i,e,t);var p=-y.dot(r,i)/d;return p<0?null:(l||(l=new b),u&&b.set(u,1-c-v,c,v),y.scaleAndAdd(l.array,h,f,p),l)}})(),applyTransform:function(e){b.add(this.direction,this.direction,this.origin),b.transformMat4(this.origin,this.origin,e),b.transformMat4(this.direction,this.direction,e),b.sub(this.direction,this.direction,this.origin),b.normalize(this.direction,this.direction)},copy:function(e){b.copy(this.origin,e.origin),b.copy(this.direction,e.direction)},clone:function(){var e=new wt;return e.copy(this),e}};var M={};M.create=function(){var e=new Se(4);return e[0]=0,e[1]=0,e[2]=0,e[3]=0,e};M.clone=function(e){var t=new Se(4);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t};M.fromValues=function(e,t,r,i){var n=new Se(4);return n[0]=e,n[1]=t,n[2]=r,n[3]=i,n};M.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e};M.set=function(e,t,r,i,n){return e[0]=t,e[1]=r,e[2]=i,e[3]=n,e};M.add=function(e,t,r){return e[0]=t[0]+r[0],e[1]=t[1]+r[1],e[2]=t[2]+r[2],e[3]=t[3]+r[3],e};M.subtract=function(e,t,r){return e[0]=t[0]-r[0],e[1]=t[1]-r[1],e[2]=t[2]-r[2],e[3]=t[3]-r[3],e};M.sub=M.subtract;M.multiply=function(e,t,r){return e[0]=t[0]*r[0],e[1]=t[1]*r[1],e[2]=t[2]*r[2],e[3]=t[3]*r[3],e};M.mul=M.multiply;M.divide=function(e,t,r){return e[0]=t[0]/r[0],e[1]=t[1]/r[1],e[2]=t[2]/r[2],e[3]=t[3]/r[3],e};M.div=M.divide;M.min=function(e,t,r){return e[0]=Math.min(t[0],r[0]),e[1]=Math.min(t[1],r[1]),e[2]=Math.min(t[2],r[2]),e[3]=Math.min(t[3],r[3]),e};M.max=function(e,t,r){return e[0]=Math.max(t[0],r[0]),e[1]=Math.max(t[1],r[1]),e[2]=Math.max(t[2],r[2]),e[3]=Math.max(t[3],r[3]),e};M.scale=function(e,t,r){return e[0]=t[0]*r,e[1]=t[1]*r,e[2]=t[2]*r,e[3]=t[3]*r,e};M.scaleAndAdd=function(e,t,r,i){return e[0]=t[0]+r[0]*i,e[1]=t[1]+r[1]*i,e[2]=t[2]+r[2]*i,e[3]=t[3]+r[3]*i,e};M.distance=function(e,t){var r=t[0]-e[0],i=t[1]-e[1],n=t[2]-e[2],a=t[3]-e[3];return Math.sqrt(r*r+i*i+n*n+a*a)};M.dist=M.distance;M.squaredDistance=function(e,t){var r=t[0]-e[0],i=t[1]-e[1],n=t[2]-e[2],a=t[3]-e[3];return r*r+i*i+n*n+a*a};M.sqrDist=M.squaredDistance;M.length=function(e){var t=e[0],r=e[1],i=e[2],n=e[3];return Math.sqrt(t*t+r*r+i*i+n*n)};M.len=M.length;M.squaredLength=function(e){var t=e[0],r=e[1],i=e[2],n=e[3];return t*t+r*r+i*i+n*n};M.sqrLen=M.squaredLength;M.negate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e[2]=-t[2],e[3]=-t[3],e};M.inverse=function(e,t){return e[0]=1/t[0],e[1]=1/t[1],e[2]=1/t[2],e[3]=1/t[3],e};M.normalize=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=r*r+i*i+n*n+a*a;return o>0&&(o=1/Math.sqrt(o),e[0]=t[0]*o,e[1]=t[1]*o,e[2]=t[2]*o,e[3]=t[3]*o),e};M.dot=function(e,t){return e[0]*t[0]+e[1]*t[1]+e[2]*t[2]+e[3]*t[3]};M.lerp=function(e,t,r,i){var n=t[0],a=t[1],o=t[2],s=t[3];return e[0]=n+i*(r[0]-n),e[1]=a+i*(r[1]-a),e[2]=o+i*(r[2]-o),e[3]=s+i*(r[3]-s),e};M.random=function(e,t){return t=t||1,e[0]=Ut(),e[1]=Ut(),e[2]=Ut(),e[3]=Ut(),M.normalize(e,e),M.scale(e,e,t),e};M.transformMat4=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3];return e[0]=r[0]*i+r[4]*n+r[8]*a+r[12]*o,e[1]=r[1]*i+r[5]*n+r[9]*a+r[13]*o,e[2]=r[2]*i+r[6]*n+r[10]*a+r[14]*o,e[3]=r[3]*i+r[7]*n+r[11]*a+r[15]*o,e};M.transformQuat=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=r[0],s=r[1],l=r[2],u=r[3],f=u*i+s*a-l*n,h=u*n+l*i-o*a,d=u*a+o*n-s*i,c=-o*i-s*n-l*a;return e[0]=f*u+c*-o+h*-l-d*-s,e[1]=h*u+c*-s+d*-o-f*-l,e[2]=d*u+c*-l+f*-s-h*-o,e};M.forEach=(function(){var e=M.create();return function(t,r,i,n,a,o){var s,l;for(r||(r=4),i||(i=0),n?l=Math.min(n*r+i,t.length):l=t.length,s=i;s<l;s+=r)e[0]=t[s],e[1]=t[s+1],e[2]=t[s+2],e[3]=t[s+3],a(e,e,o),t[s]=e[0],t[s+1]=e[1],t[s+2]=e[2],t[s+3]=e[3];return t}})();var k={};k.create=function(){var e=new Se(9);return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=1,e[5]=0,e[6]=0,e[7]=0,e[8]=1,e};k.fromMat4=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[4],e[4]=t[5],e[5]=t[6],e[6]=t[8],e[7]=t[9],e[8]=t[10],e};k.clone=function(e){var t=new Se(9);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t[4]=e[4],t[5]=e[5],t[6]=e[6],t[7]=e[7],t[8]=e[8],t};k.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4],e[5]=t[5],e[6]=t[6],e[7]=t[7],e[8]=t[8],e};k.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=0,e[4]=1,e[5]=0,e[6]=0,e[7]=0,e[8]=1,e};k.transpose=function(e,t){if(e===t){var r=t[1],i=t[2],n=t[5];e[1]=t[3],e[2]=t[6],e[3]=r,e[5]=t[7],e[6]=i,e[7]=n}else e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8];return e};k.invert=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=t[4],s=t[5],l=t[6],u=t[7],f=t[8],h=f*o-s*u,d=-f*a+s*l,c=u*a-o*l,v=r*h+i*d+n*c;return v?(v=1/v,e[0]=h*v,e[1]=(-f*i+n*u)*v,e[2]=(s*i-n*o)*v,e[3]=d*v,e[4]=(f*r-n*l)*v,e[5]=(-s*r+n*a)*v,e[6]=c*v,e[7]=(-u*r+i*l)*v,e[8]=(o*r-i*a)*v,e):null};k.adjoint=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=t[4],s=t[5],l=t[6],u=t[7],f=t[8];return e[0]=o*f-s*u,e[1]=n*u-i*f,e[2]=i*s-n*o,e[3]=s*l-a*f,e[4]=r*f-n*l,e[5]=n*a-r*s,e[6]=a*u-o*l,e[7]=i*l-r*u,e[8]=r*o-i*a,e};k.determinant=function(e){var t=e[0],r=e[1],i=e[2],n=e[3],a=e[4],o=e[5],s=e[6],l=e[7],u=e[8];return t*(u*a-o*l)+r*(-u*n+o*s)+i*(l*n-a*s)};k.multiply=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=t[6],f=t[7],h=t[8],d=r[0],c=r[1],v=r[2],p=r[3],m=r[4],_=r[5],x=r[6],T=r[7],g=r[8];return e[0]=d*i+c*o+v*u,e[1]=d*n+c*s+v*f,e[2]=d*a+c*l+v*h,e[3]=p*i+m*o+_*u,e[4]=p*n+m*s+_*f,e[5]=p*a+m*l+_*h,e[6]=x*i+T*o+g*u,e[7]=x*n+T*s+g*f,e[8]=x*a+T*l+g*h,e};k.mul=k.multiply;k.translate=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=t[6],f=t[7],h=t[8],d=r[0],c=r[1];return e[0]=i,e[1]=n,e[2]=a,e[3]=o,e[4]=s,e[5]=l,e[6]=d*i+c*o+u,e[7]=d*n+c*s+f,e[8]=d*a+c*l+h,e};k.rotate=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=t[6],f=t[7],h=t[8],d=Math.sin(r),c=Math.cos(r);return e[0]=c*i+d*o,e[1]=c*n+d*s,e[2]=c*a+d*l,e[3]=c*o-d*i,e[4]=c*s-d*n,e[5]=c*l-d*a,e[6]=u,e[7]=f,e[8]=h,e};k.scale=function(e,t,r){var i=r[0],n=r[1];return e[0]=i*t[0],e[1]=i*t[1],e[2]=i*t[2],e[3]=n*t[3],e[4]=n*t[4],e[5]=n*t[5],e[6]=t[6],e[7]=t[7],e[8]=t[8],e};k.fromMat2d=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=0,e[3]=t[2],e[4]=t[3],e[5]=0,e[6]=t[4],e[7]=t[5],e[8]=1,e};k.fromQuat=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=r+r,s=i+i,l=n+n,u=r*o,f=i*o,h=i*s,d=n*o,c=n*s,v=n*l,p=a*o,m=a*s,_=a*l;return e[0]=1-h-v,e[3]=f-_,e[6]=d+m,e[1]=f+_,e[4]=1-u-v,e[7]=c-p,e[2]=d-m,e[5]=c+p,e[8]=1-u-h,e};k.normalFromMat4=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=t[4],s=t[5],l=t[6],u=t[7],f=t[8],h=t[9],d=t[10],c=t[11],v=t[12],p=t[13],m=t[14],_=t[15],x=r*s-i*o,T=r*l-n*o,g=r*u-a*o,E=i*l-n*s,S=i*u-a*s,C=n*u-a*l,A=f*p-h*v,N=f*m-d*v,H=f*_-c*v,R=h*m-d*p,U=h*_-c*p,V=d*_-c*m,I=x*V-T*U+g*R+E*H-S*N+C*A;return I?(I=1/I,e[0]=(s*V-l*U+u*R)*I,e[1]=(l*H-o*V-u*N)*I,e[2]=(o*U-s*H+u*A)*I,e[3]=(n*U-i*V-a*R)*I,e[4]=(r*V-n*H+a*N)*I,e[5]=(i*H-r*U-a*A)*I,e[6]=(p*C-m*S+_*E)*I,e[7]=(m*g-v*C-_*T)*I,e[8]=(v*S-p*g+_*x)*I,e):null};k.frob=function(e){return Math.sqrt(Math.pow(e[0],2)+Math.pow(e[1],2)+Math.pow(e[2],2)+Math.pow(e[3],2)+Math.pow(e[4],2)+Math.pow(e[5],2)+Math.pow(e[6],2)+Math.pow(e[7],2)+Math.pow(e[8],2))};var B={};B.create=function(){var e=new Se(4);return e[0]=0,e[1]=0,e[2]=0,e[3]=1,e};B.rotationTo=(function(){var e=y.create(),t=y.fromValues(1,0,0),r=y.fromValues(0,1,0);return function(i,n,a){var o=y.dot(n,a);return o<-.999999?(y.cross(e,t,n),y.length(e)<1e-6&&y.cross(e,r,n),y.normalize(e,e),B.setAxisAngle(i,e,Math.PI),i):o>.999999?(i[0]=0,i[1]=0,i[2]=0,i[3]=1,i):(y.cross(e,n,a),i[0]=e[0],i[1]=e[1],i[2]=e[2],i[3]=1+o,B.normalize(i,i))}})();B.setAxes=(function(){var e=k.create();return function(t,r,i,n){return e[0]=i[0],e[3]=i[1],e[6]=i[2],e[1]=n[0],e[4]=n[1],e[7]=n[2],e[2]=-r[0],e[5]=-r[1],e[8]=-r[2],B.normalize(t,B.fromMat3(t,e))}})();B.clone=M.clone;B.fromValues=M.fromValues;B.copy=M.copy;B.set=M.set;B.identity=function(e){return e[0]=0,e[1]=0,e[2]=0,e[3]=1,e};B.setAxisAngle=function(e,t,r){r=r*.5;var i=Math.sin(r);return e[0]=i*t[0],e[1]=i*t[1],e[2]=i*t[2],e[3]=Math.cos(r),e};B.add=M.add;B.multiply=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=r[0],l=r[1],u=r[2],f=r[3];return e[0]=i*f+o*s+n*u-a*l,e[1]=n*f+o*l+a*s-i*u,e[2]=a*f+o*u+i*l-n*s,e[3]=o*f-i*s-n*l-a*u,e};B.mul=B.multiply;B.scale=M.scale;B.rotateX=function(e,t,r){r*=.5;var i=t[0],n=t[1],a=t[2],o=t[3],s=Math.sin(r),l=Math.cos(r);return e[0]=i*l+o*s,e[1]=n*l+a*s,e[2]=a*l-n*s,e[3]=o*l-i*s,e};B.rotateY=function(e,t,r){r*=.5;var i=t[0],n=t[1],a=t[2],o=t[3],s=Math.sin(r),l=Math.cos(r);return e[0]=i*l-a*s,e[1]=n*l+o*s,e[2]=a*l+i*s,e[3]=o*l-n*s,e};B.rotateZ=function(e,t,r){r*=.5;var i=t[0],n=t[1],a=t[2],o=t[3],s=Math.sin(r),l=Math.cos(r);return e[0]=i*l+n*s,e[1]=n*l-i*s,e[2]=a*l+o*s,e[3]=o*l-a*s,e};B.calculateW=function(e,t){var r=t[0],i=t[1],n=t[2];return e[0]=r,e[1]=i,e[2]=n,e[3]=Math.sqrt(Math.abs(1-r*r-i*i-n*n)),e};B.dot=M.dot;B.lerp=M.lerp;B.slerp=function(e,t,r,i){var n=t[0],a=t[1],o=t[2],s=t[3],l=r[0],u=r[1],f=r[2],h=r[3],d,c,v,p,m;return c=n*l+a*u+o*f+s*h,c<0&&(c=-c,l=-l,u=-u,f=-f,h=-h),1-c>1e-6?(d=Math.acos(c),v=Math.sin(d),p=Math.sin((1-i)*d)/v,m=Math.sin(i*d)/v):(p=1-i,m=i),e[0]=p*n+m*l,e[1]=p*a+m*u,e[2]=p*o+m*f,e[3]=p*s+m*h,e};B.invert=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=r*r+i*i+n*n+a*a,s=o?1/o:0;return e[0]=-r*s,e[1]=-i*s,e[2]=-n*s,e[3]=a*s,e};B.conjugate=function(e,t){return e[0]=-t[0],e[1]=-t[1],e[2]=-t[2],e[3]=t[3],e};B.length=M.length;B.len=B.length;B.squaredLength=M.squaredLength;B.sqrLen=B.squaredLength;B.normalize=M.normalize;B.fromMat3=function(e,t){var r=t[0]+t[4]+t[8],i;if(r>0)i=Math.sqrt(r+1),e[3]=.5*i,i=.5/i,e[0]=(t[5]-t[7])*i,e[1]=(t[6]-t[2])*i,e[2]=(t[1]-t[3])*i;else{var n=0;t[4]>t[0]&&(n=1),t[8]>t[n*3+n]&&(n=2);var a=(n+1)%3,o=(n+2)%3;i=Math.sqrt(t[n*3+n]-t[a*3+a]-t[o*3+o]+1),e[n]=.5*i,i=.5/i,e[3]=(t[a*3+o]-t[o*3+a])*i,e[a]=(t[a*3+n]+t[n*3+a])*i,e[o]=(t[o*3+n]+t[n*3+o])*i}return e};var F=function(){this._axisX=new b,this._axisY=new b,this._axisZ=new b,this.array=D.create(),this._dirty=!0};F.prototype={constructor:F,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},adjoint:function(){return D.adjoint(this.array,this.array),this._dirty=!0,this},clone:function(){return new F().copy(this)},copy:function(e){return D.copy(this.array,e.array),this._dirty=!0,this},determinant:function(){return D.determinant(this.array)},fromQuat:function(e){return D.fromQuat(this.array,e.array),this._dirty=!0,this},fromRotationTranslation:function(e,t){return D.fromRotationTranslation(this.array,e.array,t.array),this._dirty=!0,this},fromMat2d:function(e){return F.fromMat2d(this,e),this},frustum:function(e,t,r,i,n,a){return D.frustum(this.array,e,t,r,i,n,a),this._dirty=!0,this},identity:function(){return D.identity(this.array),this._dirty=!0,this},invert:function(){return D.invert(this.array,this.array),this._dirty=!0,this},lookAt:function(e,t,r){return D.lookAt(this.array,e.array,t.array,r.array),this._dirty=!0,this},mul:function(e){return D.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return D.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return D.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return D.multiply(this.array,e.array,this.array),this._dirty=!0,this},ortho:function(e,t,r,i,n,a){return D.ortho(this.array,e,t,r,i,n,a),this._dirty=!0,this},perspective:function(e,t,r,i){return D.perspective(this.array,e,t,r,i),this._dirty=!0,this},rotate:function(e,t){return D.rotate(this.array,this.array,e,t.array),this._dirty=!0,this},rotateX:function(e){return D.rotateX(this.array,this.array,e),this._dirty=!0,this},rotateY:function(e){return D.rotateY(this.array,this.array,e),this._dirty=!0,this},rotateZ:function(e){return D.rotateZ(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return D.scale(this.array,this.array,e.array),this._dirty=!0,this},translate:function(e){return D.translate(this.array,this.array,e.array),this._dirty=!0,this},transpose:function(){return D.transpose(this.array,this.array),this._dirty=!0,this},decomposeMatrix:(function(){var e=y.create(),t=y.create(),r=y.create(),i=k.create();return function(n,a,o){var s=this.array;y.set(e,s[0],s[1],s[2]),y.set(t,s[4],s[5],s[6]),y.set(r,s[8],s[9],s[10]);var l=y.length(e),u=y.length(t),f=y.length(r),h=this.determinant();h<0&&(l=-l),n&&n.set(l,u,f),o.set(s[12],s[13],s[14]),k.fromMat4(i,s),i[0]/=l,i[1]/=l,i[2]/=l,i[3]/=u,i[4]/=u,i[5]/=u,i[6]/=f,i[7]/=f,i[8]/=f,B.fromMat3(a.array,i),B.normalize(a.array,a.array),a._dirty=!0,o._dirty=!0}})(),toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};var _r=Object.defineProperty;if(_r){var ti=F.prototype;_r(ti,"z",{get:function(){var e=this.array;return this._axisZ.set(e[8],e[9],e[10]),this._axisZ},set:function(e){var t=this.array;e=e.array,t[8]=e[0],t[9]=e[1],t[10]=e[2],this._dirty=!0}}),_r(ti,"y",{get:function(){var e=this.array;return this._axisY.set(e[4],e[5],e[6]),this._axisY},set:function(e){var t=this.array;e=e.array,t[4]=e[0],t[5]=e[1],t[6]=e[2],this._dirty=!0}}),_r(ti,"x",{get:function(){var e=this.array;return this._axisX.set(e[0],e[1],e[2]),this._axisX},set:function(e){var t=this.array;e=e.array,t[0]=e[0],t[1]=e[1],t[2]=e[2],this._dirty=!0}})}F.adjoint=function(e,t){return D.adjoint(e.array,t.array),e._dirty=!0,e};F.copy=function(e,t){return D.copy(e.array,t.array),e._dirty=!0,e};F.determinant=function(e){return D.determinant(e.array)};F.identity=function(e){return D.identity(e.array),e._dirty=!0,e};F.ortho=function(e,t,r,i,n,a,o){return D.ortho(e.array,t,r,i,n,a,o),e._dirty=!0,e};F.perspective=function(e,t,r,i,n){return D.perspective(e.array,t,r,i,n),e._dirty=!0,e};F.lookAt=function(e,t,r,i){return D.lookAt(e.array,t.array,r.array,i.array),e._dirty=!0,e};F.invert=function(e,t){return D.invert(e.array,t.array),e._dirty=!0,e};F.mul=function(e,t,r){return D.mul(e.array,t.array,r.array),e._dirty=!0,e};F.multiply=F.mul;F.fromQuat=function(e,t){return D.fromQuat(e.array,t.array),e._dirty=!0,e};F.fromRotationTranslation=function(e,t,r){return D.fromRotationTranslation(e.array,t.array,r.array),e._dirty=!0,e};F.fromMat2d=function(i,r){i._dirty=!0;var r=r.array,i=i.array;return i[0]=r[0],i[4]=r[2],i[12]=r[4],i[1]=r[1],i[5]=r[3],i[13]=r[5],i};F.rotate=function(e,t,r,i){return D.rotate(e.array,t.array,r,i.array),e._dirty=!0,e};F.rotateX=function(e,t,r){return D.rotateX(e.array,t.array,r),e._dirty=!0,e};F.rotateY=function(e,t,r){return D.rotateY(e.array,t.array,r),e._dirty=!0,e};F.rotateZ=function(e,t,r){return D.rotateZ(e.array,t.array,r),e._dirty=!0,e};F.scale=function(e,t,r){return D.scale(e.array,t.array,r.array),e._dirty=!0,e};F.transpose=function(e,t){return D.transpose(e.array,t.array),e._dirty=!0,e};F.translate=function(e,t,r){return D.translate(e.array,t.array,r.array),e._dirty=!0,e};var ee=function(e,t,r,i){e=e||0,t=t||0,r=r||0,i=i===void 0?1:i,this.array=B.fromValues(e,t,r,i),this._dirty=!0};ee.prototype={constructor:ee,add:function(e){return B.add(this.array,this.array,e.array),this._dirty=!0,this},calculateW:function(){return B.calculateW(this.array,this.array),this._dirty=!0,this},set:function(e,t,r,i){return this.array[0]=e,this.array[1]=t,this.array[2]=r,this.array[3]=i,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this.array[2]=e[2],this.array[3]=e[3],this._dirty=!0,this},clone:function(){return new ee(this.x,this.y,this.z,this.w)},conjugate:function(){return B.conjugate(this.array,this.array),this._dirty=!0,this},copy:function(e){return B.copy(this.array,e.array),this._dirty=!0,this},dot:function(e){return B.dot(this.array,e.array)},fromMat3:function(e){return B.fromMat3(this.array,e.array),this._dirty=!0,this},fromMat4:(function(){var e=k.create();return function(t){return k.fromMat4(e,t.array),k.transpose(e,e),B.fromMat3(this.array,e),this._dirty=!0,this}})(),identity:function(){return B.identity(this.array),this._dirty=!0,this},invert:function(){return B.invert(this.array,this.array),this._dirty=!0,this},len:function(){return B.len(this.array)},length:function(){return B.length(this.array)},lerp:function(e,t,r){return B.lerp(this.array,e.array,t.array,r),this._dirty=!0,this},mul:function(e){return B.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return B.multiply(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return B.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return B.multiply(this.array,e.array,this.array),this._dirty=!0,this},normalize:function(){return B.normalize(this.array,this.array),this._dirty=!0,this},rotateX:function(e){return B.rotateX(this.array,this.array,e),this._dirty=!0,this},rotateY:function(e){return B.rotateY(this.array,this.array,e),this._dirty=!0,this},rotateZ:function(e){return B.rotateZ(this.array,this.array,e),this._dirty=!0,this},rotationTo:function(e,t){return B.rotationTo(this.array,e.array,t.array),this._dirty=!0,this},setAxes:function(e,t,r){return B.setAxes(this.array,e.array,t.array,r.array),this._dirty=!0,this},setAxisAngle:function(e,t){return B.setAxisAngle(this.array,e.array,t),this._dirty=!0,this},slerp:function(e,t,r){return B.slerp(this.array,e.array,t.array,r),this._dirty=!0,this},sqrLen:function(){return B.sqrLen(this.array)},squaredLength:function(){return B.squaredLength(this.array)},fromEuler:function(e,t){return ee.fromEuler(this,e,t)},toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};var Qt=Object.defineProperty;if(Qt){var gr=ee.prototype;Qt(gr,"x",{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),Qt(gr,"y",{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}}),Qt(gr,"z",{get:function(){return this.array[2]},set:function(e){this.array[2]=e,this._dirty=!0}}),Qt(gr,"w",{get:function(){return this.array[3]},set:function(e){this.array[3]=e,this._dirty=!0}})}ee.add=function(e,t,r){return B.add(e.array,t.array,r.array),e._dirty=!0,e};ee.set=function(e,t,r,i,n){B.set(e.array,t,r,i,n),e._dirty=!0};ee.copy=function(e,t){return B.copy(e.array,t.array),e._dirty=!0,e};ee.calculateW=function(e,t){return B.calculateW(e.array,t.array),e._dirty=!0,e};ee.conjugate=function(e,t){return B.conjugate(e.array,t.array),e._dirty=!0,e};ee.identity=function(e){return B.identity(e.array),e._dirty=!0,e};ee.invert=function(e,t){return B.invert(e.array,t.array),e._dirty=!0,e};ee.dot=function(e,t){return B.dot(e.array,t.array)};ee.len=function(e){return B.length(e.array)};ee.lerp=function(e,t,r,i){return B.lerp(e.array,t.array,r.array,i),e._dirty=!0,e};ee.slerp=function(e,t,r,i){return B.slerp(e.array,t.array,r.array,i),e._dirty=!0,e};ee.mul=function(e,t,r){return B.multiply(e.array,t.array,r.array),e._dirty=!0,e};ee.multiply=ee.mul;ee.rotateX=function(e,t,r){return B.rotateX(e.array,t.array,r),e._dirty=!0,e};ee.rotateY=function(e,t,r){return B.rotateY(e.array,t.array,r),e._dirty=!0,e};ee.rotateZ=function(e,t,r){return B.rotateZ(e.array,t.array,r),e._dirty=!0,e};ee.setAxisAngle=function(e,t,r){return B.setAxisAngle(e.array,t.array,r),e._dirty=!0,e};ee.normalize=function(e,t){return B.normalize(e.array,t.array),e._dirty=!0,e};ee.sqrLen=function(e){return B.sqrLen(e.array)};ee.squaredLength=ee.sqrLen;ee.fromMat3=function(e,t){return B.fromMat3(e.array,t.array),e._dirty=!0,e};ee.setAxes=function(e,t,r,i){return B.setAxes(e.array,t.array,r.array,i.array),e._dirty=!0,e};ee.rotationTo=function(e,t,r){return B.rotationTo(e.array,t.array,r.array),e._dirty=!0,e};ee.fromEuler=function(e,t,f){e._dirty=!0,t=t.array;var i=e.array,n=Math.cos(t[0]/2),a=Math.cos(t[1]/2),o=Math.cos(t[2]/2),s=Math.sin(t[0]/2),l=Math.sin(t[1]/2),u=Math.sin(t[2]/2),f=(f||"XYZ").toUpperCase();switch(f){case"XYZ":i[0]=s*a*o+n*l*u,i[1]=n*l*o-s*a*u,i[2]=n*a*u+s*l*o,i[3]=n*a*o-s*l*u;break;case"YXZ":i[0]=s*a*o+n*l*u,i[1]=n*l*o-s*a*u,i[2]=n*a*u-s*l*o,i[3]=n*a*o+s*l*u;break;case"ZXY":i[0]=s*a*o-n*l*u,i[1]=n*l*o+s*a*u,i[2]=n*a*u+s*l*o,i[3]=n*a*o-s*l*u;break;case"ZYX":i[0]=s*a*o-n*l*u,i[1]=n*l*o+s*a*u,i[2]=n*a*u-s*l*o,i[3]=n*a*o+s*l*u;break;case"YZX":i[0]=s*a*o+n*l*u,i[1]=n*l*o+s*a*u,i[2]=n*a*u-s*l*o,i[3]=n*a*o-s*l*u;break;case"XZY":i[0]=s*a*o-n*l*u,i[1]=n*l*o-s*a*u,i[2]=n*a*u+s*l*o,i[3]=n*a*o+s*l*u;break}};var lt=y.set,yr=y.copy,Ee=function(e,t){this.min=e||new b(1/0,1/0,1/0),this.max=t||new b(-1/0,-1/0,-1/0),this.vertices=null};Ee.prototype={constructor:Ee,updateFromVertices:function(e){if(e.length>0){var t=this.min,r=this.max,i=t.array,n=r.array;yr(i,e[0]),yr(n,e[0]);for(var a=1;a<e.length;a++){var o=e[a];o[0]<i[0]&&(i[0]=o[0]),o[1]<i[1]&&(i[1]=o[1]),o[2]<i[2]&&(i[2]=o[2]),o[0]>n[0]&&(n[0]=o[0]),o[1]>n[1]&&(n[1]=o[1]),o[2]>n[2]&&(n[2]=o[2])}t._dirty=!0,r._dirty=!0}},union:function(e){var t=this.min,r=this.max;return y.min(t.array,t.array,e.min.array),y.max(r.array,r.array,e.max.array),t._dirty=!0,r._dirty=!0,this},intersection:function(e){var t=this.min,r=this.max;return y.max(t.array,t.array,e.min.array),y.min(r.array,r.array,e.max.array),t._dirty=!0,r._dirty=!0,this},intersectBoundingBox:function(e){var t=this.min.array,r=this.max.array,i=e.min.array,n=e.max.array;return!(t[0]>n[0]||t[1]>n[1]||t[2]>n[2]||r[0]<i[0]||r[1]<i[1]||r[2]<i[2])},containBoundingBox:function(e){var t=this.min.array,r=this.max.array,i=e.min.array,n=e.max.array;return t[0]<=i[0]&&t[1]<=i[1]&&t[2]<=i[2]&&r[0]>=n[0]&&r[1]>=n[1]&&r[2]>=n[2]},containPoint:function(e){var t=this.min.array,r=this.max.array,i=e.array;return t[0]<=i[0]&&t[1]<=i[1]&&t[2]<=i[2]&&r[0]>=i[0]&&r[1]>=i[1]&&r[2]>=i[2]},isFinite:function(){var e=this.min.array,t=this.max.array;return isFinite(e[0])&&isFinite(e[1])&&isFinite(e[2])&&isFinite(t[0])&&isFinite(t[1])&&isFinite(t[2])},applyTransform:function(e){this.transformFrom(this,e)},transformFrom:(function(){var e=y.create(),t=y.create(),r=y.create(),i=y.create(),n=y.create(),a=y.create();return function(o,s){var l=o.min.array,u=o.max.array,f=s.array;return e[0]=f[0]*l[0],e[1]=f[1]*l[0],e[2]=f[2]*l[0],t[0]=f[0]*u[0],t[1]=f[1]*u[0],t[2]=f[2]*u[0],r[0]=f[4]*l[1],r[1]=f[5]*l[1],r[2]=f[6]*l[1],i[0]=f[4]*u[1],i[1]=f[5]*u[1],i[2]=f[6]*u[1],n[0]=f[8]*l[2],n[1]=f[9]*l[2],n[2]=f[10]*l[2],a[0]=f[8]*u[2],a[1]=f[9]*u[2],a[2]=f[10]*u[2],l=this.min.array,u=this.max.array,l[0]=Math.min(e[0],t[0])+Math.min(r[0],i[0])+Math.min(n[0],a[0])+f[12],l[1]=Math.min(e[1],t[1])+Math.min(r[1],i[1])+Math.min(n[1],a[1])+f[13],l[2]=Math.min(e[2],t[2])+Math.min(r[2],i[2])+Math.min(n[2],a[2])+f[14],u[0]=Math.max(e[0],t[0])+Math.max(r[0],i[0])+Math.max(n[0],a[0])+f[12],u[1]=Math.max(e[1],t[1])+Math.max(r[1],i[1])+Math.max(n[1],a[1])+f[13],u[2]=Math.max(e[2],t[2])+Math.max(r[2],i[2])+Math.max(n[2],a[2])+f[14],this.min._dirty=!0,this.max._dirty=!0,this}})(),applyProjection:function(e){var t=this.min.array,r=this.max.array,i=e.array,n=t[0],a=t[1],o=t[2],s=r[0],l=r[1],u=t[2],f=r[0],h=r[1],d=r[2];if(i[15]===1)t[0]=i[0]*n+i[12],t[1]=i[5]*a+i[13],r[2]=i[10]*o+i[14],r[0]=i[0]*f+i[12],r[1]=i[5]*h+i[13],t[2]=i[10]*d+i[14];else{var c=-1/o;t[0]=i[0]*n*c,t[1]=i[5]*a*c,r[2]=(i[10]*o+i[14])*c,c=-1/u,r[0]=i[0]*s*c,r[1]=i[5]*l*c,c=-1/d,t[2]=(i[10]*d+i[14])*c}return this.min._dirty=!0,this.max._dirty=!0,this},updateVertices:function(){var e=this.vertices;if(!e){e=[];for(var t=0;t<8;t++)e[t]=y.fromValues(0,0,0);this.vertices=e}var r=this.min.array,i=this.max.array;return lt(e[0],r[0],r[1],r[2]),lt(e[1],r[0],i[1],r[2]),lt(e[2],i[0],r[1],r[2]),lt(e[3],i[0],i[1],r[2]),lt(e[4],r[0],r[1],i[2]),lt(e[5],r[0],i[1],i[2]),lt(e[6],i[0],r[1],i[2]),lt(e[7],i[0],i[1],i[2]),this},copy:function(e){var t=this.min,r=this.max;return yr(t.array,e.min.array),yr(r.array,e.max.array),t._dirty=!0,r._dirty=!0,this},clone:function(){var e=new Ee;return e.copy(this),e}};var Yo=0,Ye=be.extend({name:"",position:null,rotation:null,scale:null,worldTransform:null,localTransform:null,autoUpdateLocalTransform:!0,_parent:null,_scene:null,_needsUpdateWorldTransform:!0,_inIterating:!1,__depth:0},function(){this.name||(this.name=(this.type||"NODE")+"_"+Yo++),this.position||(this.position=new b),this.rotation||(this.rotation=new ee),this.scale||(this.scale=new b(1,1,1)),this.worldTransform=new F,this.localTransform=new F,this._children=[]},{target:null,invisible:!1,isSkinnedMesh:function(){return!1},isRenderable:function(){return!1},setName:function(e){var t=this._scene;if(t){var r=t._nodeRepository;delete r[this.name],r[e]=this}this.name=e},add:function(e){var t=e._parent;if(t!==this){t&&t.remove(e),e._parent=this,this._children.push(e);var r=this._scene;r&&r!==e.scene&&e.traverse(this._addSelfToScene,this),e._needsUpdateWorldTransform=!0}},remove:function(e){var t=this._children,r=t.indexOf(e);r<0||(t.splice(r,1),e._parent=null,this._scene&&e.traverse(this._removeSelfFromScene,this))},removeAll:function(){for(var e=this._children,t=0;t<e.length;t++)e[t]._parent=null,this._scene&&e[t].traverse(this._removeSelfFromScene,this);this._children=[]},getScene:function(){return this._scene},getParent:function(){return this._parent},_removeSelfFromScene:function(e){e._scene.removeFromScene(e),e._scene=null},_addSelfToScene:function(e){this._scene.addToScene(e),e._scene=this._scene},isAncestor:function(e){for(var t=e._parent;t;){if(t===this)return!0;t=t._parent}return!1},children:function(){return this._children.slice()},childAt:function(e){return this._children[e]},getChildByName:function(e){for(var t=this._children,r=0;r<t.length;r++)if(t[r].name===e)return t[r]},getDescendantByName:function(e){for(var t=this._children,r=0;r<t.length;r++){var i=t[r];if(i.name===e)return i;var n=i.getDescendantByName(e);if(n)return n}},queryNode:function(e){if(e){for(var t=e.split("/"),r=this,i=0;i<t.length;i++){var n=t[i];if(n){for(var a=!1,o=r._children,s=0;s<o.length;s++){var l=o[s];if(l.name===n){r=l,a=!0;break}}if(!a)return}}return r}},getPath:function(e){if(!this._parent)return"/";for(var t=this._parent,r=this.name;t._parent&&(r=t.name+"/"+r,t._parent!=e);)t=t._parent;return!t._parent&&e?null:r},traverse:function(e,t){e.call(t,this);for(var r=this._children,i=0,n=r.length;i<n;i++)r[i].traverse(e,t)},eachChild:function(e,t){for(var r=this._children,i=0,n=r.length;i<n;i++){var a=r[i];e.call(t,a,i)}},setLocalTransform:function(e){D.copy(this.localTransform.array,e.array),this.decomposeLocalTransform()},decomposeLocalTransform:function(e){var t=e?null:this.scale;this.localTransform.decomposeMatrix(t,this.rotation,this.position)},setWorldTransform:function(e){D.copy(this.worldTransform.array,e.array),this.decomposeWorldTransform()},decomposeWorldTransform:(function(){var e=D.create();return function(t){var r=this.localTransform,i=this.worldTransform;this._parent?(D.invert(e,this._parent.worldTransform.array),D.multiply(r.array,e,i.array)):D.copy(r.array,i.array);var n=t?null:this.scale;r.decomposeMatrix(n,this.rotation,this.position)}})(),transformNeedsUpdate:function(){return this.position._dirty||this.rotation._dirty||this.scale._dirty},updateLocalTransform:function(){var e=this.position,t=this.rotation,r=this.scale;if(this.transformNeedsUpdate()){var i=this.localTransform.array;D.fromRotationTranslation(i,t.array,e.array),D.scale(i,i,r.array),t._dirty=!1,r._dirty=!1,e._dirty=!1,this._needsUpdateWorldTransform=!0}},_updateWorldTransformTopDown:function(){var e=this.localTransform.array,t=this.worldTransform.array;this._parent?D.multiplyAffine(t,this._parent.worldTransform.array,e):D.copy(t,e)},updateWorldTransform:function(){for(var e=this;e&&e.getParent()&&e.getParent().transformNeedsUpdate();)e=e.getParent();e.update()},update:function(e){this.autoUpdateLocalTransform?this.updateLocalTransform():e=!0,(e||this._needsUpdateWorldTransform)&&(this._updateWorldTransformTopDown(),e=!0,this._needsUpdateWorldTransform=!1);for(var t=this._children,r=0,i=t.length;r<i;r++)t[r].update(e)},getBoundingBox:(function(){function e(n){return!n.invisible&&n.geometry}var t=new Ee,r=new F,i=new F;return function(n,a){return a=a||new Ee,this._parent?F.invert(i,this._parent.worldTransform):F.identity(i),this.traverse(function(o){o.geometry&&o.geometry.boundingBox&&(t.copy(o.geometry.boundingBox),F.multiply(r,i,o.worldTransform),t.applyTransform(r),a.union(t))},this,e),a}})(),getWorldPosition:function(e){this.transformNeedsUpdate()&&this.updateWorldTransform();var t=this.worldTransform.array;if(e){var r=e.array;return r[0]=t[12],r[1]=t[13],r[2]=t[14],e}else return new b(t[12],t[13],t[14])},clone:function(){var e=new this.constructor,t=this._children;e.setName(this.name),e.position.copy(this.position),e.rotation.copy(this.rotation),e.scale.copy(this.scale);for(var r=0;r<t.length;r++)e.add(t[r].clone());return e},rotateAround:(function(){var e=new b,t=new F;return function(r,i,n){e.copy(this.position).subtract(r);var a=this.localTransform;a.identity(),a.translate(r),a.rotate(n,i),t.fromRotationTranslation(this.rotation,e),a.multiply(t),a.scale(this.scale),this.decomposeLocalTransform(),this._needsUpdateWorldTransform=!0}})(),lookAt:(function(){var e=new F;return function(t,r){e.lookAt(this.position,t,r||this.localTransform.y).invert(),this.setLocalTransform(e),this.target=t}})()}),Pe=Ye.extend({material:null,geometry:null,mode:L.TRIANGLES,_renderInfo:null},{__program:null,lightGroup:0,renderOrder:0,culling:!0,cullFace:L.BACK,frontFace:L.CCW,frustumCulling:!0,receiveShadow:!0,castShadow:!0,ignorePicking:!1,ignorePreZ:!1,ignoreGBuffer:!1,isRenderable:function(){return this.geometry&&this.material&&this.material.shader&&!this.invisible&&this.geometry.vertexCount>0},beforeRender:function(e){},afterRender:function(e,t){},getBoundingBox:function(e,t){return t=Ye.prototype.getBoundingBox.call(this,e,t),this.geometry&&this.geometry.boundingBox&&t.union(this.geometry.boundingBox),t},clone:(function(){var e=["castShadow","receiveShadow","mode","culling","cullFace","frontFace","frustumCulling","renderOrder","lineWidth","ignorePicking","ignorePreZ","ignoreGBuffer"];return function(){var t=Ye.prototype.clone.call(this);t.geometry=this.geometry,t.material=this.material;for(var r=0;r<e.length;r++){var i=e[r];t[i]!==this[i]&&(t[i]=this[i])}return t}})()});Pe.POINTS=L.POINTS;Pe.LINES=L.LINES;Pe.LINE_LOOP=L.LINE_LOOP;Pe.LINE_STRIP=L.LINE_STRIP;Pe.TRIANGLES=L.TRIANGLES;Pe.TRIANGLE_STRIP=L.TRIANGLE_STRIP;Pe.TRIANGLE_FAN=L.TRIANGLE_FAN;Pe.BACK=L.BACK;Pe.FRONT=L.FRONT;Pe.FRONT_AND_BACK=L.FRONT_AND_BACK;Pe.CW=L.CW;Pe.CCW=L.CCW;var Pi=be.extend({scene:null,camera:null,renderer:null},function(){this._ray=new wt,this._ndc=new W},{pick:function(e,t,r){var i=this.pickAll(e,t,[],r);return i[0]||null},pickAll:function(e,t,r,i){return this.renderer.screenToNDC(e,t,this._ndc),this.camera.castRay(this._ndc,this._ray),r=r||[],this._intersectNode(this.scene,r,i||!1),r.sort(this._intersectionCompareFunc),r},_intersectNode:function(e,t,r){e instanceof Pe&&e.isRenderable()&&(!e.ignorePicking||r)&&(e.mode===L.TRIANGLES&&e.geometry.isUseIndices()||e.geometry.pickByRay||e.geometry.pick)&&this._intersectRenderable(e,t);for(var i=0;i<e._children.length;i++)this._intersectNode(e._children[i],t,r)},_intersectRenderable:(function(){var e=new b,t=new b,r=new b,i=new wt,n=new F;return function(a,o){var s=a.isSkinnedMesh();i.copy(this._ray),F.invert(n,a.worldTransform),s||i.applyTransform(n);var l=a.geometry,u=s?a.skeleton.boundingBox:l.boundingBox;if(!(u&&!i.intersectBoundingBox(u))){if(l.pick){l.pick(this._ndc.x,this._ndc.y,this.renderer,this.camera,a,o);return}else if(l.pickByRay){l.pickByRay(i,a,o);return}var f=a.cullFace===L.BACK&&a.frontFace===L.CCW||a.cullFace===L.FRONT&&a.frontFace===L.CW,h,d=l.indices,c=l.attributes.position,v=l.attributes.weight,p=l.attributes.joint,m,_=[];if(!(!c||!c.value||!d)){if(s){m=a.skeleton.getSubSkinMatrices(a.__uid__,a.joints);for(var x=0;x<a.joints.length;x++){_[x]=_[x]||[];for(var T=0;T<16;T++)_[x][T]=m[x*16+T]}var g=[],E=[],S=[],C=[],A=[],N=l.attributes.skinnedPosition;(!N||!N.value)&&(l.createAttribute("skinnedPosition","f",3),N=l.attributes.skinnedPosition,N.init(l.vertexCount));for(var x=0;x<l.vertexCount;x++){c.get(x,g),v.get(x,E),p.get(x,S),E[3]=1-E[0]-E[1]-E[2],y.set(C,0,0,0);for(var T=0;T<4;T++)S[T]>=0&&E[T]>1e-4&&(y.transformMat4(A,g,_[S[T]]),y.scaleAndAdd(C,C,A,E[T]));N.set(x,C)}}for(var x=0;x<d.length;x+=3){var H=d[x],R=d[x+1],U=d[x+2],V=s?l.attributes.skinnedPosition:c;if(V.get(H,e.array),V.get(R,t.array),V.get(U,r.array),f?h=i.intersectTriangle(e,t,r,a.culling):h=i.intersectTriangle(e,r,t,a.culling),h){var I=new b;s?b.copy(I,h):b.transformMat4(I,h,a.worldTransform),o.push(new Pi.Intersection(h,I,a,[H,R,U],x/3,b.dist(I,this._ray.origin)))}}}}}})(),_intersectionCompareFunc:function(e,t){return e.distance-t.distance}});Pi.Intersection=function(e,t,r,i,n,a){this.point=e,this.pointWorld=t,this.target=r,this.triangle=i,this.triangleIndex=n,this.distance=a};var Jt="__dt__",Vt=function(){this._contextId=0,this._caches=[],this._context={}};Vt.prototype={use:function(e,t){var r=this._caches;r[e]||(r[e]={},t&&(r[e]=t())),this._contextId=e,this._context=r[e]},put:function(e,t){this._context[e]=t},get:function(e){return this._context[e]},dirty:function(e){e=e||"";var t=Jt+e;this.put(t,!0)},dirtyAll:function(e){e=e||"";for(var t=Jt+e,r=this._caches,i=0;i<r.length;i++)r[i]&&(r[i][t]=!0)},fresh:function(e){e=e||"";var t=Jt+e;this.put(t,!1)},freshAll:function(e){e=e||"";for(var t=Jt+e,r=this._caches,i=0;i<r.length;i++)r[i]&&(r[i][t]=!1)},isDirty:function(e){e=e||"";var t=Jt+e,r=this._context;return!r.hasOwnProperty(t)||r[t]===!0},deleteContext:function(e){delete this._caches[e],this._context={}},delete:function(e){delete this._context[e]},clearAll:function(){this._caches={}},getContext:function(){return this._context},eachContext:function(e,t){var r=Object.keys(this._caches);r.forEach(function(i){e&&e.call(t,i)})},miss:function(e){return!this._context.hasOwnProperty(e)}};Vt.prototype.constructor=Vt;var O=be.extend({width:512,height:512,type:L.UNSIGNED_BYTE,format:L.RGBA,wrapS:L.REPEAT,wrapT:L.REPEAT,minFilter:L.LINEAR_MIPMAP_LINEAR,magFilter:L.LINEAR,useMipmap:!0,anisotropic:1,flipY:!0,sRGB:!0,unpackAlignment:4,premultiplyAlpha:!1,dynamic:!1,NPOT:!1,__used:0},function(){this._cache=new Vt},{getWebGLTexture:function(e){var t=e.gl,r=this._cache;return r.use(e.__uid__),r.miss("webgl_texture")&&r.put("webgl_texture",t.createTexture()),this.dynamic?this.update(e):r.isDirty()&&(this.update(e),r.fresh()),r.get("webgl_texture")},bind:function(){},unbind:function(){},dirty:function(){this._cache&&this._cache.dirtyAll()},update:function(e){},updateCommon:function(e){var t=e.gl;t.pixelStorei(t.UNPACK_FLIP_Y_WEBGL,this.flipY),t.pixelStorei(t.UNPACK_PREMULTIPLY_ALPHA_WEBGL,this.premultiplyAlpha),t.pixelStorei(t.UNPACK_ALIGNMENT,this.unpackAlignment),this.format===L.DEPTH_COMPONENT&&(this.useMipmap=!1);var r=e.getGLExtension("EXT_sRGB");this.format===O.SRGB&&!r&&(this.format=O.RGB),this.format===O.SRGB_ALPHA&&!r&&(this.format=O.RGBA),this.NPOT=!this.isPowerOfTwo()},getAvailableWrapS:function(){return this.NPOT?L.CLAMP_TO_EDGE:this.wrapS},getAvailableWrapT:function(){return this.NPOT?L.CLAMP_TO_EDGE:this.wrapT},getAvailableMinFilter:function(){var e=this.minFilter;return this.NPOT||!this.useMipmap?e===L.NEAREST_MIPMAP_NEAREST||e===L.NEAREST_MIPMAP_LINEAR?L.NEAREST:e===L.LINEAR_MIPMAP_LINEAR||e===L.LINEAR_MIPMAP_NEAREST?L.LINEAR:e:e},getAvailableMagFilter:function(){return this.magFilter},nextHighestPowerOfTwo:function(e){--e;for(var t=1;t<32;t<<=1)e=e|e>>t;return e+1},dispose:function(e){var t=this._cache;t.use(e.__uid__);var r=t.get("webgl_texture");r&&e.gl.deleteTexture(r),t.deleteContext(e.__uid__)},isRenderable:function(){},isPowerOfTwo:function(){}});Object.defineProperty(O.prototype,"width",{get:function(){return this._width},set:function(e){this._width=e}});Object.defineProperty(O.prototype,"height",{get:function(){return this._height},set:function(e){this._height=e}});O.BYTE=L.BYTE;O.UNSIGNED_BYTE=L.UNSIGNED_BYTE;O.SHORT=L.SHORT;O.UNSIGNED_SHORT=L.UNSIGNED_SHORT;O.INT=L.INT;O.UNSIGNED_INT=L.UNSIGNED_INT;O.FLOAT=L.FLOAT;O.HALF_FLOAT=36193;O.UNSIGNED_INT_24_8_WEBGL=34042;O.DEPTH_COMPONENT=L.DEPTH_COMPONENT;O.DEPTH_STENCIL=L.DEPTH_STENCIL;O.ALPHA=L.ALPHA;O.RGB=L.RGB;O.RGBA=L.RGBA;O.LUMINANCE=L.LUMINANCE;O.LUMINANCE_ALPHA=L.LUMINANCE_ALPHA;O.SRGB=35904;O.SRGB_ALPHA=35906;O.COMPRESSED_RGB_S3TC_DXT1_EXT=33776;O.COMPRESSED_RGBA_S3TC_DXT1_EXT=33777;O.COMPRESSED_RGBA_S3TC_DXT3_EXT=33778;O.COMPRESSED_RGBA_S3TC_DXT5_EXT=33779;O.NEAREST=L.NEAREST;O.LINEAR=L.LINEAR;O.NEAREST_MIPMAP_NEAREST=L.NEAREST_MIPMAP_NEAREST;O.LINEAR_MIPMAP_NEAREST=L.LINEAR_MIPMAP_NEAREST;O.NEAREST_MIPMAP_LINEAR=L.NEAREST_MIPMAP_LINEAR;O.LINEAR_MIPMAP_LINEAR=L.LINEAR_MIPMAP_LINEAR;O.REPEAT=L.REPEAT;O.CLAMP_TO_EDGE=L.CLAMP_TO_EDGE;O.MIRRORED_REPEAT=L.MIRRORED_REPEAT;var Re=Pe.extend({skeleton:null,joints:null},function(){this.joints||(this.joints=[])},{offsetMatrix:null,isInstancedMesh:function(){return!1},isSkinnedMesh:function(){return!!(this.skeleton&&this.joints&&this.joints.length>0)},clone:function(){var e=Pe.prototype.clone.call(this);return e.skeleton=this.skeleton,this.joints&&(e.joints=this.joints.slice()),e}});Re.POINTS=L.POINTS;Re.LINES=L.LINES;Re.LINE_LOOP=L.LINE_LOOP;Re.LINE_STRIP=L.LINE_STRIP;Re.TRIANGLES=L.TRIANGLES;Re.TRIANGLE_STRIP=L.TRIANGLE_STRIP;Re.TRIANGLE_FAN=L.TRIANGLE_FAN;Re.BACK=L.BACK;Re.FRONT=L.FRONT;Re.FRONT_AND_BACK=L.FRONT_AND_BACK;Re.CW=L.CW;Re.CCW=L.CCW;var cr={};cr.isPowerOfTwo=function(e){return(e&e-1)===0};cr.nextPowerOfTwo=function(e){return e--,e|=e>>1,e|=e>>2,e|=e>>4,e|=e>>8,e|=e>>16,e++,e};cr.nearestPowerOfTwo=function(e){return Math.pow(2,Math.round(Math.log(e)/Math.LN2))};var vn=cr.isPowerOfTwo;function pn(e){return Math.pow(2,Math.round(Math.log(e)/Math.LN2))}function Ko(e,t){var r=pn(e.width),i=pn(e.height);t=t||document.createElement("canvas"),t.width=r,t.height=i;var n=t.getContext("2d");return n.drawImage(e.image,0,0,r,i),t}var K=O.extend(function(){return{image:null,pixels:null,mipmaps:[],convertToPOT:!1}},{textureType:"texture2D",update:function(e){var t=e.gl;t.bindTexture(t.TEXTURE_2D,this._cache.get("webgl_texture")),this.updateCommon(e);var r=this.format,i=this.type,n=!!(this.convertToPOT&&!this.mipmaps.length&&this.image&&(this.wrapS===O.REPEAT||this.wrapT===O.REPEAT)&&this.NPOT);t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_S,n?this.wrapS:this.getAvailableWrapS()),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_T,n?this.wrapT:this.getAvailableWrapT()),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MAG_FILTER,n?this.magFilter:this.getAvailableMagFilter()),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MIN_FILTER,n?this.minFilter:this.getAvailableMinFilter());var a=e.getGLExtension("EXT_texture_filter_anisotropic");if(a&&this.anisotropic>1&&t.texParameterf(t.TEXTURE_2D,a.TEXTURE_MAX_ANISOTROPY_EXT,this.anisotropic),i===36193){var o=e.getGLExtension("OES_texture_half_float");o||(i=L.FLOAT)}if(this.mipmaps.length)for(var s=this.width,l=this.height,u=0;u<this.mipmaps.length;u++){var f=this.mipmaps[u];this._updateTextureData(t,f,u,s,l,r,i,!1),s/=2,l/=2}else this._updateTextureData(t,this,0,this.width,this.height,r,i,n),this.useMipmap&&(!this.NPOT||n)&&t.generateMipmap(t.TEXTURE_2D);t.bindTexture(t.TEXTURE_2D,null)},_updateTextureData:function(e,t,r,i,n,a,o,s){if(t.image){var l=t.image;s&&(this._potCanvas=Ko(this,this._potCanvas),l=this._potCanvas),e.texImage2D(e.TEXTURE_2D,r,a,a,o,l)}else a<=O.COMPRESSED_RGBA_S3TC_DXT5_EXT&&a>=O.COMPRESSED_RGB_S3TC_DXT1_EXT?e.compressedTexImage2D(e.TEXTURE_2D,r,a,i,n,0,t.pixels):e.texImage2D(e.TEXTURE_2D,r,a,i,n,0,a,o,t.pixels)},generateMipmap:function(e){var t=e.gl;this.useMipmap&&!this.NPOT&&(t.bindTexture(t.TEXTURE_2D,this._cache.get("webgl_texture")),t.generateMipmap(t.TEXTURE_2D))},isPowerOfTwo:function(){return vn(this.width)&&vn(this.height)},isRenderable:function(){return this.image?this.image.width>0&&this.image.height>0:!!(this.width&&this.height)},bind:function(e){e.gl.bindTexture(e.gl.TEXTURE_2D,this.getWebGLTexture(e))},unbind:function(e){e.gl.bindTexture(e.gl.TEXTURE_2D,null)},load:function(e,t){var r=Q.createImage();t&&(r.crossOrigin=t);var i=this;return r.onload=function(){i.dirty(),i.trigger("success",i)},r.onerror=function(){i.trigger("error",i)},r.src=e,this.image=r,this}});Object.defineProperty(K.prototype,"width",{get:function(){return this.image?this.image.width:this._width},set:function(e){this.image?console.warn("Texture from image can't set width"):(this._width!==e&&this.dirty(),this._width=e)}});Object.defineProperty(K.prototype,"height",{get:function(){return this.image?this.image.height:this._height},set:function(e){this.image?console.warn("Texture from image can't set height"):(this._height!==e&&this.dirty(),this._height=e)}});function fa(e){return{byte:Q.Int8Array,ubyte:Q.Uint8Array,short:Q.Int16Array,ushort:Q.Uint16Array}[e]||Q.Float32Array}function ri(e){return"attr_"+e}function Gt(e,t,r,i){switch(this.name=e,this.type=t,this.size=r,this.semantic=i||"",this.value=null,r){case 1:this.get=function(n){return this.value[n]},this.set=function(n,a){this.value[n]=a},this.copy=function(n,a){this.value[n]=this.value[n]};break;case 2:this.get=function(n,a){var o=this.value;return a[0]=o[n*2],a[1]=o[n*2+1],a},this.set=function(n,a){var o=this.value;o[n*2]=a[0],o[n*2+1]=a[1]},this.copy=function(n,a){var o=this.value;a*=2,n*=2,o[n]=o[a],o[n+1]=o[a+1]};break;case 3:this.get=function(n,a){var o=n*3,s=this.value;return a[0]=s[o],a[1]=s[o+1],a[2]=s[o+2],a},this.set=function(n,a){var o=n*3,s=this.value;s[o]=a[0],s[o+1]=a[1],s[o+2]=a[2]},this.copy=function(n,a){var o=this.value;a*=3,n*=3,o[n]=o[a],o[n+1]=o[a+1],o[n+2]=o[a+2]};break;case 4:this.get=function(n,a){var o=this.value,s=n*4;return a[0]=o[s],a[1]=o[s+1],a[2]=o[s+2],a[3]=o[s+3],a},this.set=function(n,a){var o=this.value,s=n*4;o[s]=a[0],o[s+1]=a[1],o[s+2]=a[2],o[s+3]=a[3]},this.copy=function(n,a){var o=this.value;a*=4,n*=4,o[n]=o[a],o[n+1]=o[a+1],o[n+2]=o[a+2],o[n+3]=o[a+3]}}}Gt.prototype.init=function(e){if(!this.value||this.value.length!==e*this.size){var t=fa(this.type);this.value=new t(e*this.size)}};Gt.prototype.fromArray=function(e){var t=fa(this.type),r;if(e[0]&&e[0].length){var i=0,n=this.size;r=new t(e.length*n);for(var a=0;a<e.length;a++)for(var o=0;o<n;o++)r[i++]=e[a][o]}else r=new t(e);this.value=r};Gt.prototype.clone=function(e){var t=new Gt(this.name,this.type,this.size,this.semantic);return e&&console.warn("todo"),t};function ha(e,t,r,i,n){this.name=e,this.type=t,this.buffer=r,this.size=i,this.semantic=n,this.symbol="",this.needsRemove=!1}function ca(e){this.buffer=e,this.count=0}var Ne=be.extend(function(){return{attributes:{},indices:null,dynamic:!0,_enabledAttributes:null,__used:0}},function(){this._cache=new Vt,this._attributeList=Object.keys(this.attributes),this.__vaoCache={}},{mainAttribute:"",pick:null,pickByRay:null,dirty:function(){for(var e=this.getEnabledAttributes(),t=0;t<e.length;t++)this.dirtyAttribute(e[t]);this.dirtyIndices(),this._enabledAttributes=null,this._cache.dirty("any")},dirtyIndices:function(){this._cache.dirtyAll("indices")},dirtyAttribute:function(e){this._cache.dirtyAll(ri(e)),this._cache.dirtyAll("attributes")},getTriangleIndices:function(e,t){if(e<this.triangleCount&&e>=0){t||(t=[]);var r=this.indices;return t[0]=r[e*3],t[1]=r[e*3+1],t[2]=r[e*3+2],t}},setTriangleIndices:function(e,t){var r=this.indices;r[e*3]=t[0],r[e*3+1]=t[1],r[e*3+2]=t[2]},isUseIndices:function(){return!!this.indices},initIndicesFromArray:function(e){var t,r=this.vertexCount>65535?Q.Uint32Array:Q.Uint16Array;if(e[0]&&e[0].length){var i=0,n=3;t=new r(e.length*n);for(var a=0;a<e.length;a++)for(var o=0;o<n;o++)t[i++]=e[a][o]}else t=new r(e);this.indices=t},createAttribute:function(e,t,r,i){var n=new Gt(e,t,r,i);return this.attributes[e]&&this.removeAttribute(e),this.attributes[e]=n,this._attributeList.push(e),n},removeAttribute:function(e){var t=this._attributeList,r=t.indexOf(e);return r>=0?(t.splice(r,1),delete this.attributes[e],!0):!1},getAttribute:function(e){return this.attributes[e]},getEnabledAttributes:function(){var e=this._enabledAttributes,t=this._attributeList;if(e)return e;for(var r=[],i=this.vertexCount,n=0;n<t.length;n++){var a=t[n],o=this.attributes[a];o.value&&o.value.length===i*o.size&&r.push(a)}return this._enabledAttributes=r,r},getBufferChunks:function(e){var t=this._cache;t.use(e.__uid__);var r=t.isDirty("attributes"),i=t.isDirty("indices");if(r||i){this._updateBuffer(e.gl,r,i);for(var n=this.getEnabledAttributes(),a=0;a<n.length;a++)t.fresh(ri(n[a]));t.fresh("attributes"),t.fresh("indices")}return t.fresh("any"),t.get("chunks")},_updateBuffer:function(e,t,r){var i=this._cache,n=i.get("chunks"),a=!1;n||(n=[],n[0]={attributeBuffers:[],indicesBuffer:null},i.put("chunks",n),a=!0);var o=n[0],s=o.attributeBuffers,l=o.indicesBuffer;if(t||a){var u=this.getEnabledAttributes(),f={};if(!a)for(var h=0;h<s.length;h++)f[s[h].name]=s[h];for(var d=0;d<u.length;d++){var c=u[d],v=this.attributes[c],p;a||(p=f[c]);var m;p?m=p.buffer:m=e.createBuffer(),i.isDirty(ri(c))&&(e.bindBuffer(e.ARRAY_BUFFER,m),e.bufferData(e.ARRAY_BUFFER,v.value,this.dynamic?e.DYNAMIC_DRAW:e.STATIC_DRAW)),s[d]=new ha(c,v.type,m,v.size,v.semantic)}for(var h=d;h<s.length;h++)e.deleteBuffer(s[h].buffer);s.length=d}this.isUseIndices()&&(r||a)&&(l||(l=new ca(e.createBuffer()),o.indicesBuffer=l),l.count=this.indices.length,e.bindBuffer(e.ELEMENT_ARRAY_BUFFER,l.buffer),e.bufferData(e.ELEMENT_ARRAY_BUFFER,this.indices,this.dynamic?e.DYNAMIC_DRAW:e.STATIC_DRAW))},dispose:function(e){var t=this._cache;t.use(e.__uid__);var r=t.get("chunks");if(r)for(var i=0;i<r.length;i++){for(var n=r[i],a=0;a<n.attributeBuffers.length;a++){var o=n.attributeBuffers[a];e.gl.deleteBuffer(o.buffer)}n.indicesBuffer&&e.gl.deleteBuffer(n.indicesBuffer.buffer)}if(this.__vaoCache){var s=e.getGLExtension("OES_vertex_array_object");for(var l in this.__vaoCache){var u=this.__vaoCache[l].vao;u&&s.deleteVertexArrayOES(u)}}this.__vaoCache={},t.deleteContext(e.__uid__)}});Object.defineProperty&&(Object.defineProperty(Ne.prototype,"vertexCount",{enumerable:!1,get:function(){var e=this.attributes[this.mainAttribute];return e||(e=this.attributes[this._attributeList[0]]),!e||!e.value?0:e.value.length/e.size}}),Object.defineProperty(Ne.prototype,"triangleCount",{enumerable:!1,get:function(){var e=this.indices;return e?e.length/3:0}}));Ne.STATIC_DRAW=L.STATIC_DRAW;Ne.DYNAMIC_DRAW=L.DYNAMIC_DRAW;Ne.STREAM_DRAW=L.STREAM_DRAW;Ne.AttributeBuffer=ha;Ne.IndicesBuffer=ca;Ne.Attribute=Gt;var Le=y.create,Rt=y.add,mt=y.set,je=Ne.Attribute,J=Ne.extend(function(){return{attributes:{position:new je("position","float",3,"POSITION"),texcoord0:new je("texcoord0","float",2,"TEXCOORD_0"),texcoord1:new je("texcoord1","float",2,"TEXCOORD_1"),normal:new je("normal","float",3,"NORMAL"),tangent:new je("tangent","float",4,"TANGENT"),color:new je("color","float",4,"COLOR"),weight:new je("weight","float",3,"WEIGHT"),joint:new je("joint","float",4,"JOINT"),barycentric:new je("barycentric","float",3,null)},boundingBox:null}},{mainAttribute:"position",updateBoundingBox:function(){var e=this.boundingBox;e||(e=this.boundingBox=new Ee);var t=this.attributes.position.value;if(t&&t.length){var r=e.min,i=e.max,n=r.array,a=i.array;y.set(n,t[0],t[1],t[2]),y.set(a,t[0],t[1],t[2]);for(var o=3;o<t.length;){var s=t[o++],l=t[o++],u=t[o++];s<n[0]&&(n[0]=s),l<n[1]&&(n[1]=l),u<n[2]&&(n[2]=u),s>a[0]&&(a[0]=s),l>a[1]&&(a[1]=l),u>a[2]&&(a[2]=u)}r._dirty=!0,i._dirty=!0}},generateVertexNormals:function(){if(this.vertexCount){var e=this.indices,t=this.attributes,r=t.position.value,i=t.normal.value;if(!i||i.length!==r.length)i=t.normal.value=new Q.Float32Array(r.length);else for(var n=0;n<i.length;n++)i[n]=0;for(var a=Le(),o=Le(),s=Le(),l=Le(),u=Le(),f=Le(),h=e?e.length:this.vertexCount,d,c,v,p=0;p<h;){e?(d=e[p++],c=e[p++],v=e[p++]):(d=p++,c=p++,v=p++),mt(a,r[d*3],r[d*3+1],r[d*3+2]),mt(o,r[c*3],r[c*3+1],r[c*3+2]),mt(s,r[v*3],r[v*3+1],r[v*3+2]),y.sub(l,a,o),y.sub(u,o,s),y.cross(f,l,u);for(var n=0;n<3;n++)i[d*3+n]=i[d*3+n]+f[n],i[c*3+n]=i[c*3+n]+f[n],i[v*3+n]=i[v*3+n]+f[n]}for(var n=0;n<i.length;)mt(f,i[n],i[n+1],i[n+2]),y.normalize(f,f),i[n++]=f[0],i[n++]=f[1],i[n++]=f[2];this.dirty()}},generateFaceNormals:function(){if(this.vertexCount){this.isUniqueVertex()||this.generateUniqueVertex();var e=this.indices,t=this.attributes,r=t.position.value,i=t.normal.value,n=Le(),a=Le(),o=Le(),s=Le(),l=Le(),u=Le();i||(i=t.normal.value=new Float32Array(r.length));for(var f=e?e.length:this.vertexCount,h,d,c,v=0;v<f;){e?(h=e[v++],d=e[v++],c=e[v++]):(h=v++,d=v++,c=v++),mt(n,r[h*3],r[h*3+1],r[h*3+2]),mt(a,r[d*3],r[d*3+1],r[d*3+2]),mt(o,r[c*3],r[c*3+1],r[c*3+2]),y.sub(s,n,a),y.sub(l,a,o),y.cross(u,s,l),y.normalize(u,u);for(var p=0;p<3;p++)i[h*3+p]=u[p],i[d*3+p]=u[p],i[c*3+p]=u[p]}this.dirty()}},generateTangents:function(){if(this.vertexCount){var e=this.vertexCount,t=this.attributes;t.tangent.value||(t.tangent.value=new Float32Array(e*4));var r=t.texcoord0.value,i=t.position.value,n=t.tangent.value,a=t.normal.value;if(!r){console.warn("Geometry without texcoords can't generate tangents.");return}for(var o=[],s=[],l=0;l<e;l++)o[l]=[0,0,0],s[l]=[0,0,0];for(var u=[0,0,0],f=[0,0,0],h=this.indices,d=h?h.length:this.vertexCount,c,v,p,l=0;l<d;){h?(c=h[l++],v=h[l++],p=h[l++]):(c=l++,v=l++,p=l++);var m=r[c*2],_=r[v*2],x=r[p*2],T=r[c*2+1],g=r[v*2+1],E=r[p*2+1],S=i[c*3],C=i[v*3],A=i[p*3],N=i[c*3+1],H=i[v*3+1],R=i[p*3+1],U=i[c*3+2],V=i[v*3+2],I=i[p*3+2],G=C-S,X=A-S,q=H-N,ie=R-N,_e=V-U,we=I-U,ce=_-m,xe=x-m,de=g-T,Ae=E-T,Be=1/(ce*Ae-de*xe);u[0]=(Ae*G-de*X)*Be,u[1]=(Ae*q-de*ie)*Be,u[2]=(Ae*_e-de*we)*Be,f[0]=(ce*X-xe*G)*Be,f[1]=(ce*ie-xe*q)*Be,f[2]=(ce*we-xe*_e)*Be,Rt(o[c],o[c],u),Rt(o[v],o[v],u),Rt(o[p],o[p],u),Rt(s[c],s[c],f),Rt(s[v],s[v],f),Rt(s[p],s[p],f)}for(var Oe=Le(),Yt=Le(),qe=Le(),l=0;l<e;l++){qe[0]=a[l*3],qe[1]=a[l*3+1],qe[2]=a[l*3+2];var Mt=o[l];y.scale(Oe,qe,y.dot(qe,Mt)),y.sub(Oe,Mt,Oe),y.normalize(Oe,Oe),y.cross(Yt,qe,Mt),n[l*4]=Oe[0],n[l*4+1]=Oe[1],n[l*4+2]=Oe[2],n[l*4+3]=y.dot(Yt,s[l])<0?-1:1}this.dirty()}},isUniqueVertex:function(){return this.isUseIndices()?this.vertexCount===this.indices.length:!0},generateUniqueVertex:function(){if(!(!this.vertexCount||!this.indices)){this.indices.length>65535&&(this.indices=new Q.Uint32Array(this.indices));for(var e=this.attributes,t=this.indices,r=this.getEnabledAttributes(),i={},n=0;n<r.length;n++){var a=r[n];i[a]=e[a].value,e[a].init(this.indices.length)}for(var o=0,s=0;s<t.length;s++){for(var l=t[s],n=0;n<r.length;n++)for(var a=r[n],u=e[a].value,f=e[a].size,h=0;h<f;h++)u[o*f+h]=i[a][l*f+h];t[s]=o,o++}this.dirty()}},generateBarycentric:function(){if(this.vertexCount){this.isUniqueVertex()||this.generateUniqueVertex();var e=this.attributes,t=e.barycentric.value,r=this.indices;if(!(t&&t.length===r.length*3)){t=e.barycentric.value=new Float32Array(r.length*3);for(var i=0;i<(r?r.length:this.vertexCount/3);)for(var n=0;n<3;n++){var a=r?r[i++]:i*3+n;t[a*3+n]=1}this.dirty()}}},applyTransform:function(e){var t=this.attributes,r=t.position.value,i=t.normal.value,n=t.tangent.value;e=e.array;var a=D.create();D.invert(a,e),D.transpose(a,a);var o=y.transformMat4,s=y.forEach;s(r,3,0,null,o,e),i&&s(i,3,0,null,o,a),n&&s(n,4,0,null,o,a),this.boundingBox&&this.updateBoundingBox()},dispose:function(e){var t=this._cache;t.use(e.__uid__);var r=t.get("chunks");if(r)for(var i=0;i<r.length;i++){for(var n=r[i],a=0;a<n.attributeBuffers.length;a++){var o=n.attributeBuffers[a];e.gl.deleteBuffer(o.buffer)}n.indicesBuffer&&e.gl.deleteBuffer(n.indicesBuffer.buffer)}if(this.__vaoCache){var s=e.getGLExtension("OES_vertex_array_object");for(var l in this.__vaoCache){var u=this.__vaoCache[l].vao;u&&s.deleteVertexArrayOES(u)}}this.__vaoCache={},t.deleteContext(e.__uid__)}});J.STATIC_DRAW=Ne.STATIC_DRAW;J.DYNAMIC_DRAW=Ne.DYNAMIC_DRAW;J.STREAM_DRAW=Ne.STREAM_DRAW;J.AttributeBuffer=Ne.AttributeBuffer;J.IndicesBuffer=Ne.IndicesBuffer;J.Attribute=je;const Qo=`vec3 calcAmbientSHLight(int idx, vec3 N) {
 int offset = 9 * idx;
 return ambientSHLightCoefficients[0]
 + ambientSHLightCoefficients[1] * N.x
 + ambientSHLightCoefficients[2] * N.y
 + ambientSHLightCoefficients[3] * N.z
 + ambientSHLightCoefficients[4] * N.x * N.z
 + ambientSHLightCoefficients[5] * N.z * N.y
 + ambientSHLightCoefficients[6] * N.y * N.x
 + ambientSHLightCoefficients[7] * (3.0 * N.z * N.z - 1.0)
 + ambientSHLightCoefficients[8] * (N.x * N.x - N.y * N.y);
}`;var Ge="uniform vec3 ",$t="uniform float ",Ot="@export clay.header.",It="@end",Te=":unconfigurable;";const Jo=[Ot+"directional_light",Ge+"directionalLightDirection[DIRECTIONAL_LIGHT_COUNT]"+Te,Ge+"directionalLightColor[DIRECTIONAL_LIGHT_COUNT]"+Te,It,Ot+"ambient_light",Ge+"ambientLightColor[AMBIENT_LIGHT_COUNT]"+Te,It,Ot+"ambient_sh_light",Ge+"ambientSHLightColor[AMBIENT_SH_LIGHT_COUNT]"+Te,Ge+"ambientSHLightCoefficients[AMBIENT_SH_LIGHT_COUNT * 9]"+Te,Qo,It,Ot+"ambient_cubemap_light",Ge+"ambientCubemapLightColor[AMBIENT_CUBEMAP_LIGHT_COUNT]"+Te,"uniform samplerCube ambientCubemapLightCubemap[AMBIENT_CUBEMAP_LIGHT_COUNT]"+Te,"uniform sampler2D ambientCubemapLightBRDFLookup[AMBIENT_CUBEMAP_LIGHT_COUNT]"+Te,It,Ot+"point_light",Ge+"pointLightPosition[POINT_LIGHT_COUNT]"+Te,$t+"pointLightRange[POINT_LIGHT_COUNT]"+Te,Ge+"pointLightColor[POINT_LIGHT_COUNT]"+Te,It,Ot+"spot_light",Ge+"spotLightPosition[SPOT_LIGHT_COUNT]"+Te,Ge+"spotLightDirection[SPOT_LIGHT_COUNT]"+Te,$t+"spotLightRange[SPOT_LIGHT_COUNT]"+Te,$t+"spotLightUmbraAngleCosine[SPOT_LIGHT_COUNT]"+Te,$t+"spotLightPenumbraAngleCosine[SPOT_LIGHT_COUNT]"+Te,$t+"spotLightFalloffFactor[SPOT_LIGHT_COUNT]"+Te,Ge+"spotLightColor[SPOT_LIGHT_COUNT]"+Te,It].join(`
`);z.import(Jo);var Xe=Ye.extend(function(){return{color:[1,1,1],intensity:1,castShadow:!0,shadowResolution:512,group:0}},{type:"",clone:function(){var e=Ye.prototype.clone.call(this);return e.color=Array.prototype.slice.call(this.color),e.intensity=this.intensity,e.castShadow=this.castShadow,e.shadowResolution=this.shadowResolution,e}}),or=function(e,t){this.normal=e||new b(0,1,0),this.distance=t||0};or.prototype={constructor:or,distanceToPoint:function(e){return y.dot(e.array,this.normal.array)-this.distance},projectPoint:function(e,t){t||(t=new b);var r=this.distanceToPoint(e);return y.scaleAndAdd(t.array,e.array,this.normal.array,-r),t._dirty=!0,t},normalize:function(){var e=1/y.len(this.normal.array);y.scale(this.normal.array,e),this.distance*=e},intersectFrustum:function(e){for(var t=e.vertices,r=this.normal.array,i=y.dot(t[0].array,r)>this.distance,n=1;n<8;n++)if(y.dot(t[n].array,r)>this.distance!=i)return!0},intersectLine:(function(){var e=y.create();return function(t,r,i){var n=this.distanceToPoint(t),a=this.distanceToPoint(r);if(n>0&&a>0||n<0&&a<0)return null;var o=this.normal.array,s=this.distance,l=t.array;y.sub(e,r.array,t.array),y.normalize(e,e);var u=y.dot(o,e);if(u===0)return null;i||(i=new b);var f=(y.dot(o,l)-s)/u;return y.scaleAndAdd(i.array,l,e,-f),i._dirty=!0,i}})(),applyTransform:(function(){var e=D.create(),t=M.create(),r=M.create();return r[3]=1,function(i){i=i.array,y.scale(r,this.normal.array,this.distance),M.transformMat4(r,r,i),this.distance=y.dot(r,this.normal.array),D.invert(e,i),D.transpose(e,e),t[3]=0,y.copy(t,this.normal.array),M.transformMat4(t,t,e),y.copy(this.normal.array,t)}})(),copy:function(e){y.copy(this.normal.array,e.normal.array),this.normal._dirty=!0,this.distance=e.distance},clone:function(){var e=new or;return e.copy(this),e}};var fe=y.set,mn=y.copy,_n=y.transformMat4,ii=Math.min,ni=Math.max,Hr=function(){this.planes=[];for(var e=0;e<6;e++)this.planes.push(new or);this.boundingBox=new Ee,this.vertices=[];for(var e=0;e<8;e++)this.vertices[e]=y.fromValues(0,0,0)};Hr.prototype={setFromProjection:function(e){var t=this.planes,r=e.array,i=r[0],n=r[1],a=r[2],o=r[3],s=r[4],l=r[5],u=r[6],f=r[7],h=r[8],d=r[9],c=r[10],v=r[11],p=r[12],m=r[13],_=r[14],x=r[15];fe(t[0].normal.array,o-i,f-s,v-h),t[0].distance=-(x-p),t[0].normalize(),fe(t[1].normal.array,o+i,f+s,v+h),t[1].distance=-(x+p),t[1].normalize(),fe(t[2].normal.array,o+n,f+l,v+d),t[2].distance=-(x+m),t[2].normalize(),fe(t[3].normal.array,o-n,f-l,v-d),t[3].distance=-(x-m),t[3].normalize(),fe(t[4].normal.array,o-a,f-u,v-c),t[4].distance=-(x-_),t[4].normalize(),fe(t[5].normal.array,o+a,f+u,v+c),t[5].distance=-(x+_),t[5].normalize();var T=this.boundingBox,g=this.vertices;if(x===0){var E=l/i,S=-_/(c-1),C=-_/(c+1),A=-C/l,N=-S/l;T.min.set(-A*E,-A,C),T.max.set(A*E,A,S),fe(g[0],-A*E,-A,C),fe(g[1],-A*E,A,C),fe(g[2],A*E,-A,C),fe(g[3],A*E,A,C),fe(g[4],-N*E,-N,S),fe(g[5],-N*E,N,S),fe(g[6],N*E,-N,S),fe(g[7],N*E,N,S)}else{var H=(-1-p)/i,R=(1-p)/i,U=(1-m)/l,V=(-1-m)/l,I=(-1-_)/c,G=(1-_)/c;T.min.set(Math.min(H,R),Math.min(V,U),Math.min(G,I)),T.max.set(Math.max(R,H),Math.max(U,V),Math.max(I,G));var X=T.min.array,q=T.max.array;fe(g[0],X[0],X[1],X[2]),fe(g[1],X[0],q[1],X[2]),fe(g[2],q[0],X[1],X[2]),fe(g[3],q[0],q[1],X[2]),fe(g[4],X[0],X[1],q[2]),fe(g[5],X[0],q[1],q[2]),fe(g[6],q[0],X[1],q[2]),fe(g[7],q[0],q[1],q[2])}},getTransformedBoundingBox:(function(){var e=y.create();return function(t,r){var i=this.vertices,n=r.array,a=t.min,o=t.max,s=a.array,l=o.array,u=i[0];_n(e,u,n),mn(s,e),mn(l,e);for(var f=1;f<8;f++)u=i[f],_n(e,u,n),s[0]=ii(e[0],s[0]),s[1]=ii(e[1],s[1]),s[2]=ii(e[2],s[2]),l[0]=ni(e[0],l[0]),l[1]=ni(e[1],l[1]),l[2]=ni(e[2],l[2]);return a._dirty=!0,o._dirty=!0,t}})()};var kt=Ye.extend(function(){return{projectionMatrix:new F,invProjectionMatrix:new F,viewMatrix:new F,frustum:new Hr}},function(){this.update(!0)},{update:function(e){Ye.prototype.update.call(this,e),F.invert(this.viewMatrix,this.worldTransform),this.updateProjectionMatrix(),F.invert(this.invProjectionMatrix,this.projectionMatrix),this.frustum.setFromProjection(this.projectionMatrix)},setViewMatrix:function(e){F.copy(this.viewMatrix,e),F.invert(this.worldTransform,e),this.decomposeWorldTransform()},decomposeProjectionMatrix:function(){},setProjectionMatrix:function(e){F.copy(this.projectionMatrix,e),F.invert(this.invProjectionMatrix,e),this.decomposeProjectionMatrix()},updateProjectionMatrix:function(){},castRay:(function(){var e=M.create();return function(t,r){var i=r!==void 0?r:new wt,n=t.array[0],a=t.array[1];return M.set(e,n,a,-1,1),M.transformMat4(e,e,this.invProjectionMatrix.array),M.transformMat4(e,e,this.worldTransform.array),y.scale(i.origin.array,e,1/e[3]),M.set(e,n,a,1,1),M.transformMat4(e,e,this.invProjectionMatrix.array),M.transformMat4(e,e,this.worldTransform.array),y.scale(e,e,1/e[3]),y.sub(i.direction.array,e,i.origin.array),y.normalize(i.direction.array,i.direction.array),i.direction._dirty=!0,i.origin._dirty=!0,i}})()}),$o=D.create(),gn=D.create(),ai={};function es(e){var t=[],r=Object.keys(e);r.sort();for(var i=0;i<r.length;i++){var n=r[i];t.push(n+" "+e[n])}var a=t.join(`
`);if(ai[a])return ai[a];var o=he.genGUID();return ai[a]=o,o}function Vr(){this.opaque=[],this.transparent=[],this._opaqueCount=0,this._transparentCount=0}Vr.prototype.startCount=function(){this._opaqueCount=0,this._transparentCount=0};Vr.prototype.add=function(e,t){t?this.transparent[this._transparentCount++]=e:this.opaque[this._opaqueCount++]=e};Vr.prototype.endCount=function(){this.transparent.length=this._transparentCount,this.opaque.length=this._opaqueCount};var vt=Ye.extend(function(){return{material:null,lights:[],viewBoundingBoxLastFrame:new Ee,shadowUniforms:{},_cameraList:[],_lightUniforms:{},_previousLightNumber:{},_lightNumber:{},_lightProgramKeys:{},_nodeRepository:{},_renderLists:new Lt(20)}},function(){this._scene=this},{addToScene:function(e){e instanceof kt?(this._cameraList.length>0&&console.warn("Found multiple camera in one scene. Use the fist one."),this._cameraList.push(e)):e instanceof Xe&&this.lights.push(e),e.name&&(this._nodeRepository[e.name]=e)},removeFromScene:function(e){var t;e instanceof kt?(t=this._cameraList.indexOf(e),t>=0&&this._cameraList.splice(t,1)):e instanceof Xe&&(t=this.lights.indexOf(e),t>=0&&this.lights.splice(t,1)),e.name&&delete this._nodeRepository[e.name]},getNode:function(e){return this._nodeRepository[e]},setMainCamera:function(e){var t=this._cameraList.indexOf(e);t>=0&&this._cameraList.splice(t,1),this._cameraList.unshift(e)},getMainCamera:function(){return this._cameraList[0]},getLights:function(){return this.lights},updateLights:function(){var e=this.lights;this._previousLightNumber=this._lightNumber;for(var t={},r=0;r<e.length;r++){var i=e[r];if(!i.invisible){var n=i.group;t[n]||(t[n]={}),t[n][i.type]=t[n][i.type]||0,t[n][i.type]++}}this._lightNumber=t;for(var a in t)this._lightProgramKeys[a]=es(t[a]);this._updateLightUniforms()},cloneNode:function(e){var t=e.clone(),r={};function i(n,a){r[n.__uid__]=a;for(var o=0;o<n._children.length;o++){var s=n._children[o],l=a._children[o];i(s,l)}}return i(e,t),t.traverse(function(n){n.skeleton&&(n.skeleton=n.skeleton.clone(r)),n.material&&(n.material=n.material.clone())}),t},updateRenderList:function(e,t){var r=e.__uid__,i=this._renderLists.get(r);i||(i=new Vr,this._renderLists.put(r,i)),i.startCount(),t&&(this.viewBoundingBoxLastFrame.min.set(1/0,1/0,1/0),this.viewBoundingBoxLastFrame.max.set(-1/0,-1/0,-1/0));var n=this.material&&this.material.transparent||!1;return this._doUpdateRenderList(this,e,n,i,t),i.endCount(),i},getRenderList:function(e){return this._renderLists.get(e.__uid__)},_doUpdateRenderList:function(e,t,r,i,n){if(!e.invisible)for(var a=0;a<e._children.length;a++){var o=e._children[a];if(o.isRenderable()){var s=o.isSkinnedMesh()?$o:o.worldTransform.array,l=o.geometry;D.multiplyAffine(gn,t.viewMatrix.array,s),(n&&!l.boundingBox||!this.isFrustumCulled(o,t,gn))&&i.add(o,o.material.transparent||r)}o._children.length>0&&this._doUpdateRenderList(o,t,r,i,n)}},isFrustumCulled:(function(){var e=new Ee,t=new F;return function(r,i,n){var a=r.boundingBox;if(a||(r.skeleton&&r.skeleton.boundingBox?a=r.skeleton.boundingBox:a=r.geometry.boundingBox),!a)return!1;if(t.array=n,e.transformFrom(a,t),r.castShadow&&this.viewBoundingBoxLastFrame.union(e),r.frustumCulling){if(!e.intersectBoundingBox(i.frustum.boundingBox))return!0;t.array=i.projectionMatrix.array,e.max.array[2]>0&&e.min.array[2]<0&&(e.max.array[2]=-1e-20),e.applyProjection(t);var o=e.min.array,s=e.max.array;if(s[0]<-1||o[0]>1||s[1]<-1||o[1]>1||s[2]<-1||o[2]>1)return!0}return!1}})(),_updateLightUniforms:function(){var e=this.lights;e.sort(ts);var t=this._lightUniforms;for(var r in t)for(var i in t[r])t[r][i].value.length=0;for(var n=0;n<e.length;n++){var a=e[n];if(!a.invisible){var r=a.group;for(var i in a.uniformTemplates){var o=a.uniformTemplates[i],s=o.value(a);if(s!=null){t[r]||(t[r]={}),t[r][i]||(t[r][i]={type:"",value:[]});var l=t[r][i];switch(l.type=o.type+"v",o.type){case"1i":case"1f":case"t":l.value.push(s);break;case"2f":case"3f":case"4f":for(var u=0;u<s.length;u++)l.value.push(s[u]);break;default:console.error("Unkown light uniform type "+o.type)}}}}}},getLightGroups:function(){var e=[];for(var t in this._lightNumber)e.push(t);return e},getNumberChangedLightGroups:function(){var e=[];for(var t in this._lightNumber)this.isLightNumberChanged(t)&&e.push(t);return e},isLightNumberChanged:function(e){var t=this._previousLightNumber,r=this._lightNumber;for(var i in r[e])if(!t[e]||r[e][i]!==t[e][i])return!0;for(var i in t[e])if(!r[e]||r[e][i]!==t[e][i])return!0;return!1},getLightsNumbers:function(e){return this._lightNumber[e]},getProgramKey:function(e){return this._lightProgramKeys[e]},setLightUniforms:(function(){function e(t,r,i){for(var n in t){var a=t[n];if(a.type==="tv"){if(!r.hasUniform(n))continue;for(var o=[],s=0;s<a.value.length;s++){var l=a.value[s],u=r.takeCurrentTextureSlot(i,l);o.push(u)}r.setUniform(i.gl,"1iv",n,o)}else r.setUniform(i.gl,a.type,n,a.value)}}return function(t,r,i){e(this._lightUniforms[r],t,i),e(this.shadowUniforms,t,i)}})(),dispose:function(){this.material=null,this._opaqueList=[],this._transparentList=[],this.lights=[],this._lightUniforms={},this._lightNumber={},this._nodeRepository={}}});function ts(e,t){if(t.castShadow&&!e.castShadow)return!0}var xr=cr.isPowerOfTwo,rs=["px","nx","py","ny","pz","nz"],At=O.extend(function(){return{image:{px:null,nx:null,py:null,ny:null,pz:null,nz:null},pixels:{px:null,nx:null,py:null,ny:null,pz:null,nz:null},mipmaps:[]}},{textureType:"textureCube",update:function(e){var t=e.gl;t.bindTexture(t.TEXTURE_CUBE_MAP,this._cache.get("webgl_texture")),this.updateCommon(e);var r=this.format,i=this.type;t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_WRAP_S,this.getAvailableWrapS()),t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_WRAP_T,this.getAvailableWrapT()),t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_MAG_FILTER,this.getAvailableMagFilter()),t.texParameteri(t.TEXTURE_CUBE_MAP,t.TEXTURE_MIN_FILTER,this.getAvailableMinFilter());var n=e.getGLExtension("EXT_texture_filter_anisotropic");if(n&&this.anisotropic>1&&t.texParameterf(t.TEXTURE_CUBE_MAP,n.TEXTURE_MAX_ANISOTROPY_EXT,this.anisotropic),i===36193){var a=e.getGLExtension("OES_texture_half_float");a||(i=L.FLOAT)}if(this.mipmaps.length)for(var o=this.width,s=this.height,l=0;l<this.mipmaps.length;l++){var u=this.mipmaps[l];this._updateTextureData(t,u,l,o,s,r,i),o/=2,s/=2}else this._updateTextureData(t,this,0,this.width,this.height,r,i),!this.NPOT&&this.useMipmap&&t.generateMipmap(t.TEXTURE_CUBE_MAP);t.bindTexture(t.TEXTURE_CUBE_MAP,null)},_updateTextureData:function(e,t,r,i,n,a,o){for(var s=0;s<6;s++){var l=rs[s],u=t.image&&t.image[l];u?e.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+s,r,a,a,o,u):e.texImage2D(e.TEXTURE_CUBE_MAP_POSITIVE_X+s,r,a,i,n,0,a,o,t.pixels&&t.pixels[l])}},generateMipmap:function(e){var t=e.gl;this.useMipmap&&!this.NPOT&&(t.bindTexture(t.TEXTURE_CUBE_MAP,this._cache.get("webgl_texture")),t.generateMipmap(t.TEXTURE_CUBE_MAP))},bind:function(e){e.gl.bindTexture(e.gl.TEXTURE_CUBE_MAP,this.getWebGLTexture(e))},unbind:function(e){e.gl.bindTexture(e.gl.TEXTURE_CUBE_MAP,null)},isPowerOfTwo:function(){return this.image.px?xr(this.image.px.width)&&xr(this.image.px.height):xr(this.width)&&xr(this.height)},isRenderable:function(){return this.image.px?Bt(this.image.px)&&Bt(this.image.nx)&&Bt(this.image.py)&&Bt(this.image.ny)&&Bt(this.image.pz)&&Bt(this.image.nz):!!(this.width&&this.height)},load:function(e,t){var r=0,i=this;return he.each(e,function(n,a){var o=Q.createImage();t&&(o.crossOrigin=t),o.onload=function(){r--,r===0&&(i.dirty(),i.trigger("success",i))},o.onerror=function(){r--},r++,o.src=n,i.image[a]=o}),this}});Object.defineProperty(At.prototype,"width",{get:function(){return this.image&&this.image.px?this.image.px.width:this._width},set:function(e){this.image&&this.image.px?console.warn("Texture from image can't set width"):(this._width!==e&&this.dirty(),this._width=e)}});Object.defineProperty(At.prototype,"height",{get:function(){return this.image&&this.image.px?this.image.px.height:this._height},set:function(e){this.image&&this.image.px?console.warn("Texture from image can't set height"):(this._height!==e&&this.dirty(),this._height=e)}});function Bt(e){return e.width>0&&e.height>0}var ge=kt.extend({fov:50,aspect:1,near:.1,far:2e3},{updateProjectionMatrix:function(){var e=this.fov/180*Math.PI;this.projectionMatrix.perspective(e,this.aspect,this.near,this.far)},decomposeProjectionMatrix:function(){var e=this.projectionMatrix.array,t=Math.atan(1/e[5])*2;this.fov=t/Math.PI*180,this.aspect=e[5]/e[0],this.near=e[14]/(e[10]-1),this.far=e[14]/(e[10]+1)},clone:function(){var e=kt.prototype.clone.call(this);return e.fov=this.fov,e.aspect=this.aspect,e.near=this.near,e.far=this.far,e}}),Tr="framebuffer",rt="renderbuffer",yn=rt+"_width",xn=rt+"_height",oi=rt+"_attached",si="depthtexture_attached",_t=L.FRAMEBUFFER,er=L.RENDERBUFFER,nr=L.DEPTH_ATTACHMENT,da=L.COLOR_ATTACHMENT0,me=be.extend({depthBuffer:!0,viewport:null,_width:0,_height:0,_textures:null,_boundRenderer:null},function(){this._cache=new Vt,this._textures={}},{getTextureWidth:function(){return this._width},getTextureHeight:function(){return this._height},bind:function(e){if(e.__currentFrameBuffer){if(e.__currentFrameBuffer===this)return;console.warn("Renderer already bound with another framebuffer. Unbind it first")}e.__currentFrameBuffer=this;var t=e.gl;t.bindFramebuffer(_t,this._getFrameBufferGL(e)),this._boundRenderer=e;var r=this._cache;r.put("viewport",e.viewport);var i=!1,n,a;for(var o in this._textures){i=!0;var s=this._textures[o];s&&(n=s.texture.width,a=s.texture.height,this._doAttach(e,s.texture,o,s.target))}this._width=n,this._height=a,!i&&this.depthBuffer&&console.error("Must attach texture before bind, or renderbuffer may have incorrect width and height."),this.viewport?e.setViewport(this.viewport):e.setViewport(0,0,n,a,1);var l=r.get("attached_textures");if(l){for(var o in l)if(!this._textures[o]){var u=l[o];this._doDetach(t,o,u)}}if(!r.get(si)&&this.depthBuffer){r.miss(rt)&&r.put(rt,t.createRenderbuffer());var f=r.get(rt);(n!==r.get(yn)||a!==r.get(xn))&&(t.bindRenderbuffer(er,f),t.renderbufferStorage(er,t.DEPTH_COMPONENT16,n,a),r.put(yn,n),r.put(xn,a),t.bindRenderbuffer(er,null)),r.get(oi)||(t.framebufferRenderbuffer(_t,nr,er,f),r.put(oi,!0))}},unbind:function(e){e.__currentFrameBuffer=null;var t=e.gl;t.bindFramebuffer(_t,null),this._boundRenderer=null,this._cache.use(e.__uid__);var r=this._cache.get("viewport");r&&e.setViewport(r),this.updateMipmap(e)},updateMipmap:function(e){var t=e.gl;for(var r in this._textures){var i=this._textures[r];if(i){var n=i.texture;if(!n.NPOT&&n.useMipmap&&n.minFilter===O.LINEAR_MIPMAP_LINEAR){var a=n.textureType==="textureCube"?L.TEXTURE_CUBE_MAP:L.TEXTURE_2D;t.bindTexture(a,n.getWebGLTexture(e)),t.generateMipmap(a),t.bindTexture(a,null)}}}},checkStatus:function(e){return e.checkFramebufferStatus(_t)},_getFrameBufferGL:function(e){var t=this._cache;return t.use(e.__uid__),t.miss(Tr)&&t.put(Tr,e.gl.createFramebuffer()),t.get(Tr)},attach:function(e,t,r){if(!e.width)throw new Error("The texture attached to color buffer is not a valid.");t=t||da,r=r||L.TEXTURE_2D;var i=this._boundRenderer,n=i&&i.gl,a;if(n){var o=this._cache;o.use(i.__uid__),a=o.get("attached_textures")}var s=this._textures[t];if(!(s&&s.target===r&&s.texture===e&&a&&a[t]!=null)){var l=!0;i&&(l=this._doAttach(i,e,t,r),this.viewport||i.setViewport(0,0,e.width,e.height,1)),l&&(this._textures[t]=this._textures[t]||{},this._textures[t].texture=e,this._textures[t].target=r)}},_doAttach:function(e,t,r,i){var n=e.gl,a=t.getWebGLTexture(e),o=this._cache.get("attached_textures");if(o&&o[r]){var s=o[r];if(s.texture===t&&s.target===i)return}r=+r;var l=!0;if(r===nr||r===L.DEPTH_STENCIL_ATTACHMENT){var u=e.getGLExtension("WEBGL_depth_texture");if(u||(console.error("Depth texture is not supported by the browser"),l=!1),t.format!==L.DEPTH_COMPONENT&&t.format!==L.DEPTH_STENCIL&&(console.error("The texture attached to depth buffer is not a valid."),l=!1),l){var f=this._cache.get(rt);f&&(n.framebufferRenderbuffer(_t,nr,er,null),n.deleteRenderbuffer(f),this._cache.put(rt,!1)),this._cache.put(oi,!1),this._cache.put(si,!0)}}return n.framebufferTexture2D(_t,r,i,a,0),o||(o={},this._cache.put("attached_textures",o)),o[r]=o[r]||{},o[r].texture=t,o[r].target=i,l},_doDetach:function(e,t,r){e.framebufferTexture2D(_t,t,r,null,0);var i=this._cache.get("attached_textures");i&&i[t]&&(i[t]=null),(t===nr||t===L.DEPTH_STENCIL_ATTACHMENT)&&this._cache.put(si,!1)},detach:function(e,t){if(this._textures[e]=null,this._boundRenderer){var r=this._cache;r.use(this._boundRenderer.__uid__),this._doDetach(this._boundRenderer.gl,e,t)}},dispose:function(e){var t=e.gl,r=this._cache;r.use(e.__uid__);var i=r.get(rt);i&&t.deleteRenderbuffer(i);var n=r.get(Tr);n&&t.deleteFramebuffer(n),r.deleteContext(e.__uid__),this._textures={}}});me.DEPTH_ATTACHMENT=nr;me.COLOR_ATTACHMENT0=da;me.STENCIL_ATTACHMENT=L.STENCIL_ATTACHMENT;me.DEPTH_STENCIL_ATTACHMENT=L.DEPTH_STENCIL_ATTACHMENT;var is=["px","nx","py","ny","pz","nz"],Ni=be.extend(function(){var e={position:new b,far:1e3,near:.1,texture:null,shadowMapPass:null},t=e._cameras={px:new ge({fov:90}),nx:new ge({fov:90}),py:new ge({fov:90}),ny:new ge({fov:90}),pz:new ge({fov:90}),nz:new ge({fov:90})};return t.px.lookAt(b.POSITIVE_X,b.NEGATIVE_Y),t.nx.lookAt(b.NEGATIVE_X,b.NEGATIVE_Y),t.py.lookAt(b.POSITIVE_Y,b.POSITIVE_Z),t.ny.lookAt(b.NEGATIVE_Y,b.NEGATIVE_Z),t.pz.lookAt(b.POSITIVE_Z,b.NEGATIVE_Y),t.nz.lookAt(b.NEGATIVE_Z,b.NEGATIVE_Y),e._frameBuffer=new me,e},{getCamera:function(e){return this._cameras[e]},render:function(e,t,r){var i=e.gl;r||t.update();for(var n=this.texture.width,a=2*Math.atan(n/(n-.5))/Math.PI*180,o=0;o<6;o++){var s=is[o],l=this._cameras[s];if(b.copy(l.position,this.position),l.far=this.far,l.near=this.near,l.fov=a,this.shadowMapPass){l.update();var u=t.getBoundingBox();u.applyTransform(l.viewMatrix),t.viewBoundingBoxLastFrame.copy(u),this.shadowMapPass.render(e,t,l,!0)}this._frameBuffer.attach(this.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+o),this._frameBuffer.bind(e),e.render(t,l,!0),this._frameBuffer.unbind(e)}},dispose:function(e){this._frameBuffer.dispose(e)}}),Ri=J.extend({dynamic:!1,widthSegments:1,heightSegments:1},function(){this.build()},{build:function(){for(var e=this.heightSegments,t=this.widthSegments,r=this.attributes,i=[],n=[],a=[],o=[],s=0;s<=e;s++)for(var l=s/e,u=0;u<=t;u++){var f=u/t;if(i.push([2*f-1,2*l-1,0]),n&&n.push([f,l]),a&&a.push([0,0,1]),u<t&&s<e){var h=u+s*(t+1);o.push([h,h+1,h+t+1]),o.push([h+t+1,h+1,h+t+2])}}r.position.fromArray(i),r.texcoord0.fromArray(n),r.normal.fromArray(a),this.initIndicesFromArray(o),this.boundingBox=new Ee,this.boundingBox.min.set(-1,-1,0),this.boundingBox.max.set(1,1,0)}}),le=new F,va=J.extend({dynamic:!1,widthSegments:1,heightSegments:1,depthSegments:1,inside:!1},function(){this.build()},{build:function(){var e={px:Ft("px",this.depthSegments,this.heightSegments),nx:Ft("nx",this.depthSegments,this.heightSegments),py:Ft("py",this.widthSegments,this.depthSegments),ny:Ft("ny",this.widthSegments,this.depthSegments),pz:Ft("pz",this.widthSegments,this.heightSegments),nz:Ft("nz",this.widthSegments,this.heightSegments)},t=["position","texcoord0","normal"],r=0,i=0;for(var n in e)r+=e[n].vertexCount,i+=e[n].indices.length;for(var a=0;a<t.length;a++)this.attributes[t[a]].init(r);this.indices=new Q.Uint16Array(i);var o=0,s=0;for(var n in e){for(var l=e[n],a=0;a<t.length;a++)for(var u=t[a],f=l.attributes[u].value,h=l.attributes[u].size,d=u==="normal",c=0;c<f.length;c++){var v=f[c];this.inside&&d&&(v=-v),this.attributes[u].value[c+h*s]=v}for(var p=l.indices.length,c=0;c<l.indices.length;c++)this.indices[c+o]=s+l.indices[this.inside?p-c-1:c];o+=l.indices.length,s+=l.vertexCount}this.boundingBox=new Ee,this.boundingBox.max.set(1,1,1),this.boundingBox.min.set(-1,-1,-1)}});function Ft(e,t,r){le.identity();var i=new Ri({widthSegments:t,heightSegments:r});switch(e){case"px":F.translate(le,le,b.POSITIVE_X),F.rotateY(le,le,Math.PI/2);break;case"nx":F.translate(le,le,b.NEGATIVE_X),F.rotateY(le,le,-Math.PI/2);break;case"py":F.translate(le,le,b.POSITIVE_Y),F.rotateX(le,le,-Math.PI/2);break;case"ny":F.translate(le,le,b.NEGATIVE_Y),F.rotateX(le,le,Math.PI/2);break;case"pz":F.translate(le,le,b.POSITIVE_Z);break;case"nz":F.translate(le,le,b.NEGATIVE_Z),F.rotateY(le,le,Math.PI);break}return i.applyTransform(le),i}const ns=`@export clay.skybox.vertex
#define SHADER_NAME skybox
uniform mat4 world : WORLD;
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
attribute vec3 position : POSITION;
varying vec3 v_WorldPosition;
void main()
{
 v_WorldPosition = (world * vec4(position, 1.0)).xyz;
 gl_Position = worldViewProjection * vec4(position, 1.0);
}
@end
@export clay.skybox.fragment
#define PI 3.1415926
uniform mat4 viewInverse : VIEWINVERSE;
#ifdef EQUIRECTANGULAR
uniform sampler2D environmentMap;
#else
uniform samplerCube environmentMap;
#endif
uniform float lod: 0.0;
varying vec3 v_WorldPosition;
@import clay.util.rgbm
@import clay.util.srgb
@import clay.util.ACES
void main()
{
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(v_WorldPosition - eyePos);
#ifdef EQUIRECTANGULAR
 float phi = acos(V.y);
 float theta = atan(-V.x, V.z) + PI * 0.5;
 vec2 uv = vec2(theta / 2.0 / PI, phi / PI);
 vec4 texel = decodeHDR(texture2D(environmentMap, fract(uv)));
#else
 #if defined(LOD) || defined(SUPPORT_TEXTURE_LOD)
 vec4 texel = decodeHDR(textureCubeLodEXT(environmentMap, V, lod));
 #else
 vec4 texel = decodeHDR(textureCube(environmentMap, V));
 #endif
#endif
#ifdef SRGB_DECODE
 texel = sRGBToLinear(texel);
#endif
#ifdef TONEMAPPING
 texel.rgb = ACESToneMapping(texel.rgb);
#endif
#ifdef SRGB_ENCODE
 texel = linearTosRGB(texel);
#endif
 gl_FragColor = encodeHDR(vec4(texel.rgb, 1.0));
}
@end`;z.import(ns);var lr=Re.extend(function(){var e=new z({vertex:z.source("clay.skybox.vertex"),fragment:z.source("clay.skybox.fragment")}),t=new at({shader:e,depthMask:!1});return{scene:null,geometry:new va,material:t,environmentMap:null,culling:!1,_dummyCamera:new ge}},function(){var e=this.scene;e&&this.attachScene(e),this.environmentMap&&this.setEnvironmentMap(this.environmentMap)},{attachScene:function(e){this.scene&&this.detachScene(),e.skybox=this,this.scene=e,e.on("beforerender",this._beforeRenderScene,this)},detachScene:function(){this.scene&&(this.scene.off("beforerender",this._beforeRenderScene),this.scene.skybox=null),this.scene=null},dispose:function(e){this.detachScene(),this.geometry.dispose(e)},setEnvironmentMap:function(e){e.textureType==="texture2D"?(this.material.define("EQUIRECTANGULAR"),e.minFilter=O.LINEAR):this.material.undefine("EQUIRECTANGULAR"),this.material.set("environmentMap",e)},getEnvironmentMap:function(){return this.material.get("environmentMap")},_beforeRenderScene:function(e,t,r){this.renderSkybox(e,r)},renderSkybox:function(e,t){var r=this._dummyCamera;r.aspect=e.getViewportAspect(),r.fov=t.fov||50,r.updateProjectionMatrix(),F.invert(r.invProjectionMatrix,r.projectionMatrix),r.worldTransform.copy(t.worldTransform),r.viewMatrix.copy(t.viewMatrix),this.position.copy(t.getWorldPosition()),this.update(),e.gl.disable(e.gl.BLEND),this.material.get("lod")>0?this.material.define("fragment","LOD"):this.material.undefine("fragment","LOD"),e.renderPass([this],r)}}),as=542327876,os=131072,ss=512,ls=4;function Oi(e){return e.charCodeAt(0)+(e.charCodeAt(1)<<8)+(e.charCodeAt(2)<<16)+(e.charCodeAt(3)<<24)}var us=31,fs=Oi("DXT1"),hs=Oi("DXT3"),cs=Oi("DXT5"),ds=0,vs=1,ps=2,ms=3,_s=4,gs=7,ys=20,xs=21,Ts=28,Es={parse:function(e,t){var r=new Int32Array(e,0,us);if(r[ds]!==as||!r(ys)&ls)return null;var i=r(xs),n=r[_s],a=r[ms],o=r[Ts]&ss,s=r[ps]&os,l,u;switch(i){case fs:l=8,u=O.COMPRESSED_RGB_S3TC_DXT1_EXT;break;case hs:l=16,u=O.COMPRESSED_RGBA_S3TC_DXT3_EXT;break;case cs:l=16,u=O.COMPRESSED_RGBA_S3TC_DXT5_EXT;break;default:return null}var f=r[vs]+4,h=o?6:1,d=1;s&&(d=Math.max(1,r[gs]));for(var c=[],v=0;v<h;v++){var p=n,m=a;c[v]=new K({width:p,height:m,format:u});for(var _=[],x=0;x<d;x++){var T=Math.max(4,p)/4*Math.max(4,m)/4*l,g=new Uint8Array(e,f,T);f+=T,p*=.5,m*=.5,_[x]=g}c[v].pixels=_[0],s&&(c[v].mipmaps=_)}if(t)t.width=c[0].width,t.height=c[0].height,t.format=c[0].format,t.pixels=c[0].pixels,t.mipmaps=c[0].mipmaps;else return c[0]}},Lr=String.fromCharCode,Ss=8,ws=32767;function bs(e,t,r,i){if(e[3]>0){var n=Math.pow(2,e[3]-128-8+i);t[r+0]=e[0]*n,t[r+1]=e[1]*n,t[r+2]=e[2]*n}else t[r+0]=0,t[r+1]=0,t[r+2]=0;return t[r+3]=1,t}function As(e,t,r){for(var i="",n=t;n<r;n++)i+=Lr(e[n]);return i}function Cs(e,t){t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3]}function Tn(e,t,r,i){for(var n=0,a=0,o=i;o>0;)if(e[a][0]=t[r++],e[a][1]=t[r++],e[a][2]=t[r++],e[a][3]=t[r++],e[a][0]===1&&e[a][1]===1&&e[a][2]===1){for(var s=e[a][3]<<n>>>0;s>0;s--)Cs(e[a-1],e[a]),a++,o--;n+=8}else a++,o--,n=0;return r}function Ls(e,t,r,i){if(i<Ss|i>ws)return Tn(e,t,r,i);var n=t[r++];if(n!=2)return Tn(e,t,r-1,i);if(e[0][1]=t[r++],e[0][2]=t[r++],n=t[r++],(e[0][2]<<8>>>0|n)>>>0!==i)return null;for(var n=0;n<4;n++)for(var a=0;a<i;){var o=t[r++];if(o>128){o=(o&127)>>>0;for(var s=t[r++];o--;)e[a++][n]=s}else for(;o--;)e[a++][n]=t[r++]}return r}var Ms={parseRGBE:function(e,t,r){r==null&&(r=0);var i=new Uint8Array(e),n=i.length;if(As(i,0,2)==="#?"){for(var a=2;a<n&&!(Lr(i[a])===`
`&&Lr(i[a+1])===`
`);a++);if(!(a>=n)){a+=2;for(var o="";a<n;a++){var s=Lr(i[a]);if(s===`
`)break;o+=s}var l=o.split(" "),u=parseInt(l[1]),f=parseInt(l[3]);if(!(!f||!u)){for(var h=a+1,d=[],c=0;c<f;c++){d[c]=[];for(var v=0;v<4;v++)d[c][v]=0}for(var p=new Float32Array(f*u*4),m=0,_=0;_<u;_++){var h=Ls(d,i,h,f);if(!h)return null;for(var c=0;c<f;c++)bs(d[c],p,m,r),m+=4}return t||(t=new K),t.width=f,t.height=u,t.pixels=p,t.type=O.FLOAT,t}}}},parseRGBEFromPNG:function(e){}},Ke={loadTexture:function(e,t,r,i){var n;if(typeof t=="function"?(r=t,i=r,t={}):t=t||{},typeof e=="string"){if(e.match(/.hdr$/)||t.fileType==="hdr")return n=new K({width:0,height:0,sRGB:!1}),Ke._fetchTexture(e,function(a){Ms.parseRGBE(a,n,t.exposure),n.dirty(),r&&r(n)},i),n;e.match(/.dds$/)||t.fileType==="dds"?(n=new K({width:0,height:0}),Ke._fetchTexture(e,function(a){Es.parse(a,n),n.dirty(),r&&r(n)},i)):(n=new K,n.load(e),n.success(r),n.error(i))}else typeof e=="object"&&typeof e.px<"u"&&(n=new At,n.load(e),n.success(r),n.error(i));return n},loadPanorama:function(e,t,r,i,n,a){var o=this;typeof i=="function"?(n=i,a=n,i={}):i=i||{},Ke.loadTexture(t,i,function(s){s.flipY=i.flipY||!1,o.panoramaToCubeMap(e,s,r,i),s.dispose(e),n&&n(r)},a)},panoramaToCubeMap:function(e,t,r,i){var n=new Ni,a=new lr({scene:new vt});return a.setEnvironmentMap(t),i=i||{},i.encodeRGBM&&a.material.define("fragment","RGBM_ENCODE"),r.sRGB=t.sRGB,n.texture=r,n.render(e,a.scene),n.texture=null,n.dispose(e),r},heightToNormal:function(e,t){var r=document.createElement("canvas"),i=r.width=e.width,n=r.height=e.height,a=r.getContext("2d");a.drawImage(e,0,0,i,n),t=t||!1;for(var o=a.getImageData(0,0,i,n),s=a.createImageData(i,n),l=0;l<o.data.length;l+=4){if(t){var u=o.data[l],f=o.data[l+1],h=o.data[l+2],d=Math.abs(u-f)+Math.abs(f-h);if(d>20)return console.warn("Given image is not a height map"),e}var c,v,p,m;l%(i*4)===0?(c=o.data[l],p=o.data[l+4]):l%(i*4)===(i-1)*4?(c=o.data[l-4],p=o.data[l]):(c=o.data[l-4],p=o.data[l+4]),l<i*4?(v=o.data[l],m=o.data[l+i*4]):l>i*(n-1)*4?(v=o.data[l-i*4],m=o.data[l]):(v=o.data[l-i*4],m=o.data[l+i*4]),s.data[l]=c-p+127,s.data[l+1]=v-m+127,s.data[l+2]=255,s.data[l+3]=255}return a.putImageData(s,0,0),r},isHeightImage:function(e,t,r){if(!e||!e.width||!e.height)return!1;var i=document.createElement("canvas"),n=i.getContext("2d"),a=t||32;r=r||20,i.width=i.height=a,n.drawImage(e,0,0,a,a);for(var o=n.getImageData(0,0,a,a),s=0;s<o.data.length;s+=4){var l=o.data[s],u=o.data[s+1],f=o.data[s+2],h=Math.abs(l-u)+Math.abs(u-f);if(h>r)return!1}return!0},_fetchTexture:function(e,t,r){Q.request.get({url:e,responseType:"arraybuffer",onload:t,onerror:r})},createChessboard:function(e,t,r,i){e=e||512,t=t||64,r=r||"black",i=i||"white";var n=Math.ceil(e/t),a=document.createElement("canvas");a.width=e,a.height=e;var o=a.getContext("2d");o.fillStyle=i,o.fillRect(0,0,e,e),o.fillStyle=r;for(var s=0;s<n;s++)for(var l=0;l<n;l++){var u=l%2?s%2:s%2-1;u&&o.fillRect(s*t,l*t,t,t)}var f=new K({image:a,anisotropic:8});return f},createBlank:function(e){var t=document.createElement("canvas");t.width=1,t.height=1;var r=t.getContext("2d");r.fillStyle=e,r.fillRect(0,0,1,1);var i=new K({image:t});return i}},Ti=["mousedown","mouseup","mousemove","mouseover","mouseout","click","dblclick","contextmenu"];function Ei(e){return"_on"+e}var Si=function(e){var t=this;this._texture=new K({anisotropic:32,flipY:!1,surface:this,dispose:function(r){t.dispose(),K.prototype.dispose.call(this,r)}}),Ti.forEach(function(r){this[Ei(r)]=function(i){i.triangle&&this._meshes.forEach(function(n){this.dispatchEvent(r,n,i.triangle,i.point)},this)}},this),this._meshes=[],e&&this.setECharts(e),this.onupdate=null};Si.prototype={constructor:Si,getTexture:function(){return this._texture},setECharts:function(e){this._chart=e;var t=e.getDom();if(!(t instanceof HTMLCanvasElement))console.error("ECharts must init on canvas if it is used as texture."),t=document.createElement("canvas");else{var r=this,i=e.getZr(),n=i.__oldRefreshImmediately||i.refreshImmediately;i.refreshImmediately=function(){n.call(this),r._texture.dirty(),r.onupdate&&r.onupdate()},i.__oldRefreshImmediately=n}this._texture.image=t,this._texture.dirty(),this.onupdate&&this.onupdate()},dispatchEvent:(function(){var e=new b,t=new b,r=new b,i=new W,n=new W,a=new W,o=new W,s=new b;return function(l,u,f,h){var d=u.geometry,c=d.attributes.position,v=d.attributes.texcoord0,p=b.dot,m=b.cross;c.get(f[0],e.array),c.get(f[1],t.array),c.get(f[2],r.array),v.get(f[0],i.array),v.get(f[1],n.array),v.get(f[2],a.array),m(s,t,r);var _=p(e,s),x=p(h,s)/_;m(s,r,e);var T=p(h,s)/_;m(s,e,t);var g=p(h,s)/_;W.scale(o,i,x),W.scaleAndAdd(o,o,n,T),W.scaleAndAdd(o,o,a,g);var E=o.x*this._chart.getWidth(),S=o.y*this._chart.getHeight();this._chart.getZr().handler.dispatch(l,{zrX:E,zrY:S})}})(),attachToMesh:function(e){this._meshes.indexOf(e)>=0||(Ti.forEach(function(t){e.on(t,this[Ei(t)],this)},this),this._meshes.push(e))},detachFromMesh:function(e){var t=this._meshes.indexOf(e);t>=0&&this._meshes.splice(t,1),Ti.forEach(function(r){e.off(r,this[Ei(r)])},this)},dispose:function(){this._meshes.forEach(function(e){this.detachFromMesh(e)},this)}};var ur=kt.extend({left:-1,right:1,near:-1,far:1,top:1,bottom:-1},{updateProjectionMatrix:function(){this.projectionMatrix.ortho(this.left,this.right,this.bottom,this.top,this.near,this.far)},decomposeProjectionMatrix:function(){var e=this.projectionMatrix.array;this.left=(-1-e[12])/e[0],this.right=(1-e[12])/e[0],this.top=(1-e[13])/e[5],this.bottom=(-1-e[13])/e[5],this.near=-(-1-e[14])/e[10],this.far=-(1-e[14])/e[10]},clone:function(){var e=kt.prototype.clone.call(this);return e.left=this.left,e.right=this.right,e.near=this.near,e.far=this.far,e.top=this.top,e.bottom=this.bottom,e}});const Ds=`
@export clay.compositor.vertex
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;
varying vec2 v_Texcoord;
void main()
{
 v_Texcoord = texcoord;
 gl_Position = worldViewProjection * vec4(position, 1.0);
}
@end`;z.import(Ds);var Ps=new Ri,En=new Re({geometry:Ps,frustumCulling:!1}),Ns=new ur,Me=be.extend(function(){return{fragment:"",outputs:null,material:null,blendWithPrevious:!1,clearColor:!1,clearDepth:!0}},function(){var e=new z(z.source("clay.compositor.vertex"),this.fragment),t=new at({shader:e});t.enableTexturesAll(),this.material=t},{setUniform:function(e,t){this.material.setUniform(e,t)},getUniform:function(e){var t=this.material.uniforms[e];if(t)return t.value},attachOutput:function(e,t){this.outputs||(this.outputs={}),t=t||L.COLOR_ATTACHMENT0,this.outputs[t]=e},detachOutput:function(e){for(var t in this.outputs)this.outputs[t]===e&&(this.outputs[t]=null)},bind:function(e,t){if(this.outputs)for(var r in this.outputs){var i=this.outputs[r];i&&t.attach(i,r)}t&&t.bind(e)},unbind:function(e,t){t.unbind(e)},render:function(e,t){var r=e.gl;if(t){this.bind(e,t);var i=e.getGLExtension("EXT_draw_buffers");if(i&&this.outputs){var n=[];for(var a in this.outputs)a=+a,a>=r.COLOR_ATTACHMENT0&&a<=r.COLOR_ATTACHMENT0+8&&n.push(a);i.drawBuffersEXT(n)}}this.trigger("beforerender",this,e);var o=this.clearDepth?r.DEPTH_BUFFER_BIT:0;if(r.depthMask(!0),this.clearColor){o=o|r.COLOR_BUFFER_BIT,r.colorMask(!0,!0,!0,!0);var s=this.clearColor;Array.isArray(s)&&r.clearColor(s[0],s[1],s[2],s[3])}r.clear(o),this.blendWithPrevious?(r.enable(r.BLEND),this.material.transparent=!0):(r.disable(r.BLEND),this.material.transparent=!1),this.renderQuad(e),this.trigger("afterrender",this,e),t&&this.unbind(e,t)},renderQuad:function(e){En.material=this.material,e.renderPass([En],Ns)},dispose:function(e){}});const Rs=`#define SAMPLE_NUMBER 1024
#define PI 3.14159265358979
uniform sampler2D normalDistribution;
uniform vec2 viewportSize : [512, 256];
const vec3 N = vec3(0.0, 0.0, 1.0);
const float fSampleNumber = float(SAMPLE_NUMBER);
vec3 importanceSampleNormal(float i, float roughness, vec3 N) {
 vec3 H = texture2D(normalDistribution, vec2(roughness, i)).rgb;
 vec3 upVector = abs(N.y) > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
 vec3 tangentX = normalize(cross(N, upVector));
 vec3 tangentZ = cross(N, tangentX);
 return normalize(tangentX * H.x + N * H.y + tangentZ * H.z);
}
float G_Smith(float roughness, float NoV, float NoL) {
 float k = roughness * roughness / 2.0;
 float G1V = NoV / (NoV * (1.0 - k) + k);
 float G1L = NoL / (NoL * (1.0 - k) + k);
 return G1L * G1V;
}
void main() {
 vec2 uv = gl_FragCoord.xy / viewportSize;
 float NoV = uv.x;
 float roughness = uv.y;
 vec3 V;
 V.x = sqrt(1.0 - NoV * NoV);
 V.y = 0.0;
 V.z = NoV;
 float A = 0.0;
 float B = 0.0;
 for (int i = 0; i < SAMPLE_NUMBER; i++) {
 vec3 H = importanceSampleNormal(float(i) / fSampleNumber, roughness, N);
 vec3 L = reflect(-V, H);
 float NoL = clamp(L.z, 0.0, 1.0);
 float NoH = clamp(H.z, 0.0, 1.0);
 float VoH = clamp(dot(V, H), 0.0, 1.0);
 if (NoL > 0.0) {
 float G = G_Smith(roughness, NoV, NoL);
 float G_Vis = G * VoH / (NoH * NoV);
 float Fc = pow(1.0 - VoH, 5.0);
 A += (1.0 - Fc) * G_Vis;
 B += Fc * G_Vis;
 }
 }
 gl_FragColor = vec4(vec2(A, B) / fSampleNumber, 0.0, 1.0);
}
`,Os=`#define SHADER_NAME prefilter
#define SAMPLE_NUMBER 1024
#define PI 3.14159265358979
uniform mat4 viewInverse : VIEWINVERSE;
uniform samplerCube environmentMap;
uniform sampler2D normalDistribution;
uniform float roughness : 0.5;
varying vec2 v_Texcoord;
varying vec3 v_WorldPosition;
@import clay.util.rgbm
vec3 importanceSampleNormal(float i, float roughness, vec3 N) {
 vec3 H = texture2D(normalDistribution, vec2(roughness, i)).rgb;
 vec3 upVector = abs(N.y) > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
 vec3 tangentX = normalize(cross(N, upVector));
 vec3 tangentZ = cross(N, tangentX);
 return normalize(tangentX * H.x + N * H.y + tangentZ * H.z);
}
void main() {
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(v_WorldPosition - eyePos);
 vec3 N = V;
 vec3 prefilteredColor = vec3(0.0);
 float totalWeight = 0.0;
 float fMaxSampleNumber = float(SAMPLE_NUMBER);
 for (int i = 0; i < SAMPLE_NUMBER; i++) {
 vec3 H = importanceSampleNormal(float(i) / fMaxSampleNumber, roughness, N);
 vec3 L = reflect(-V, H);
 float NoL = clamp(dot(N, L), 0.0, 1.0);
 if (NoL > 0.0) {
 prefilteredColor += decodeHDR(textureCube(environmentMap, L)).rgb * NoL;
 totalWeight += NoL;
 }
 }
 gl_FragColor = encodeHDR(vec4(prefilteredColor / totalWeight, 1.0));
}
`;var Qe={},li=["px","nx","py","ny","pz","nz"];Qe.prefilterEnvironmentMap=function(e,t,r,i,n){(!n||!i)&&(i=Qe.generateNormalDistribution(),n=Qe.integrateBRDF(e,i)),r=r||{};var a=r.width||64,o=r.height||64,s=r.type||t.type,l=new At({width:a,height:o,type:s,flipY:!1,mipmaps:[]});l.isPowerOfTwo()||console.warn("Width and height must be power of two to enable mipmap.");var u=Math.min(a,o),f=Math.log(u)/Math.log(2)+1,h=new at({shader:new z({vertex:z.source("clay.skybox.vertex"),fragment:Os})});h.set("normalDistribution",i),r.encodeRGBM&&h.define("fragment","RGBM_ENCODE"),r.decodeRGBM&&h.define("fragment","RGBM_DECODE");var d=new vt,c;if(t.textureType==="texture2D"){var v=new At({width:a,height:o,type:s===O.FLOAT?O.HALF_FLOAT:s});Ke.panoramaToCubeMap(e,t,v,{encodeRGBM:r.decodeRGBM}),t=v}c=new lr({scene:d,material:h}),c.material.set("environmentMap",t);var p=new Ni({texture:l});r.encodeRGBM&&(s=l.type=O.UNSIGNED_BYTE);for(var m=new K({width:a,height:o,type:s}),_=new me({depthBuffer:!1}),x=Q[s===O.UNSIGNED_BYTE?"Uint8Array":"Float32Array"],T=0;T<f;T++){l.mipmaps[T]={pixels:{}},c.material.set("roughness",T/(f-1));for(var g=m.width,E=2*Math.atan(g/(g-.5))/Math.PI*180,S=0;S<li.length;S++){var C=new x(m.width*m.height*4);_.attach(m),_.bind(e);var A=p.getCamera(li[S]);A.fov=E,e.render(d,A),e.gl.readPixels(0,0,m.width,m.height,O.RGBA,s,C),_.unbind(e),l.mipmaps[T].pixels[li[S]]=C}m.width/=2,m.height/=2,m.dirty()}return _.dispose(e),m.dispose(e),c.dispose(e),i.dispose(e),{environmentMap:l,brdfLookup:n,normalDistribution:i,maxMipmapLevel:f}};Qe.integrateBRDF=function(e,t){t=t||Qe.generateNormalDistribution();var r=new me({depthBuffer:!1}),i=new Me({fragment:Rs}),n=new K({width:512,height:256,type:O.HALF_FLOAT,wrapS:O.CLAMP_TO_EDGE,wrapT:O.CLAMP_TO_EDGE,minFilter:O.NEAREST,magFilter:O.NEAREST,useMipmap:!1});return i.setUniform("normalDistribution",t),i.setUniform("viewportSize",[512,256]),i.attachOutput(n),i.render(e,r),r.dispose(e),n};Qe.generateNormalDistribution=function(r,i){for(var r=r||256,i=i||1024,n=new K({width:r,height:i,type:O.FLOAT,minFilter:O.NEAREST,magFilter:O.NEAREST,wrapS:O.CLAMP_TO_EDGE,wrapT:O.CLAMP_TO_EDGE,useMipmap:!1}),a=new Float32Array(i*r*4),o=[],s=0;s<r;s++){for(var l=s/r,u=l*l,f=0;f<i;f++){var h=(f<<16|f>>>16)>>>0;h=((h&1431655765)<<1|(h&2863311530)>>>1)>>>0,h=((h&858993459)<<2|(h&3435973836)>>>2)>>>0,h=((h&252645135)<<4|(h&4042322160)>>>4)>>>0,h=(((h&16711935)<<8|(h&4278255360)>>>8)>>>0)/4294967296;var d=Math.sqrt((1-h)/(1+(u*u-1)*h));o[f]=d}for(var f=0;f<i;f++){var c=(f*r+s)*4,d=o[f],v=Math.sqrt(1-d*d),p=f/i,m=2*Math.PI*p;a[c]=v*Math.cos(m),a[c+1]=d,a[c+2]=v*Math.sin(m),a[c+3]=1}}return n.pixels=a,n};var Is=Xe.extend({cubemap:null,castShadow:!1,_normalDistribution:null,_brdfLookup:null},{type:"AMBIENT_CUBEMAP_LIGHT",prefilter:function(e,t){if(!e.getGLExtension("EXT_shader_texture_lod")){console.warn("Device not support textureCubeLodEXT");return}this._brdfLookup||(this._normalDistribution=Qe.generateNormalDistribution(),this._brdfLookup=Qe.integrateBRDF(e,this._normalDistribution));var r=this.cubemap;if(!r.__prefiltered){var i=Qe.prefilterEnvironmentMap(e,r,{encodeRGBM:!0,width:t,height:t},this._normalDistribution,this._brdfLookup);this.cubemap=i.environmentMap,this.cubemap.__prefiltered=!0,r.dispose(e)}},getBRDFLookup:function(){return this._brdfLookup},uniformTemplates:{ambientCubemapLightColor:{type:"3f",value:function(e){var t=e.color,r=e.intensity;return[t[0]*r,t[1]*r,t[2]*r]}},ambientCubemapLightCubemap:{type:"t",value:function(e){return e.cubemap}},ambientCubemapLightBRDFLookup:{type:"t",value:function(e){return e._brdfLookup}}}}),Bs=Xe.extend({castShadow:!1,coefficients:[]},function(){this._coefficientsTmpArr=new Q.Float32Array(27)},{type:"AMBIENT_SH_LIGHT",uniformTemplates:{ambientSHLightColor:{type:"3f",value:function(e){var t=e.color,r=e.intensity;return[t[0]*r,t[1]*r,t[2]*r]}},ambientSHLightCoefficients:{type:"3f",value:function(e){for(var t=e._coefficientsTmpArr,r=0;r<e.coefficients.length;r++)t[r]=e.coefficients[r];return t}}}}),pa={},St=["px","nx","py","ny","pz","nz"];function Fs(e,t){var r=e[0],i=e[1],n=e[2];return t===0?1:t===1?r:t===2?i:t===3?n:t===4?r*n:t===5?i*n:t===6?r*i:t===7?3*n*n-1:r*r-i*i}var Us={px:[2,1,0,-1,-1,1],nx:[2,1,0,1,-1,-1],py:[0,2,1,1,-1,-1],ny:[0,2,1,1,1,1],pz:[0,1,2,-1,-1,-1],nz:[0,1,2,1,-1,1]};function zs(e,t,r,i){for(var n=new Q.Float32Array(27),a=y.create(),o=y.create(),s=y.create(),l=0;l<9;l++){for(var u=y.create(),f=0;f<St.length;f++){for(var h=t[St[f]],d=y.create(),c=0,v=0,p=Us[St[f]],m=0;m<i;m++)for(var _=0;_<r;_++){a[0]=_/(r-1)*2-1,a[1]=m/(i-1)*2-1,a[2]=-1,y.normalize(a,a),s[0]=a[p[0]]*p[3],s[1]=a[p[1]]*p[4],s[2]=a[p[2]]*p[5],o[0]=h[v++]/255,o[1]=h[v++]/255,o[2]=h[v++]/255;var x=h[v++]/255*8.12;o[0]*=x,o[1]*=x,o[2]*=x,y.scaleAndAdd(d,d,o,Fs(s,l)*-a[2]),c+=-a[2]}y.scaleAndAdd(u,u,d,1/c)}n[l*3]=u[0]/6,n[l*3+1]=u[1]/6,n[l*3+2]=u[2]/6}return n}pa.projectEnvironmentMap=function(e,t,r){r=r||{},r.lod=r.lod||0;var i,n=new vt,a=64;t.textureType==="texture2D"?i=new lr({scene:n,environmentMap:t}):(a=t.image&&t.image.px?t.image.px.width:t.width,i=new lr({scene:n,environmentMap:t}));var o=Math.ceil(a/Math.pow(2,r.lod)),s=Math.ceil(a/Math.pow(2,r.lod)),l=new K({width:o,height:s}),u=new me;i.material.define("fragment","RGBM_ENCODE"),r.decodeRGBM&&i.material.define("fragment","RGBM_DECODE"),i.material.set("lod",r.lod);for(var f=new Ni({texture:l}),h={},d=0;d<St.length;d++){h[St[d]]=new Uint8Array(o*s*4);var c=f.getCamera(St[d]);c.fov=90,u.attach(l),u.bind(e),e.render(n,c),e.gl.readPixels(0,0,o,s,O.RGBA,O.UNSIGNED_BYTE,h[St[d]]),u.unbind(e)}return i.dispose(e),u.dispose(e),l.dispose(e),zs(e,h,o,s)};var Ce={firstNotNull:function(){for(var e=0,t=arguments.length;e<t;e++)if(arguments[e]!=null)return arguments[e]},queryDataIndex:function(e,t){if(t.dataIndexInside!=null)return t.dataIndexInside;if(t.dataIndex!=null)return $e(t.dataIndex)?ki(t.dataIndex,function(r){return e.indexOfRawIndex(r)}):e.indexOfRawIndex(t.dataIndex);if(t.name!=null)return $e(t.name)?ki(t.name,function(r){return e.indexOfName(r)}):e.indexOfName(t.name)}},Hs=J.extend({dynamic:!1,widthSegments:40,heightSegments:20,phiStart:0,phiLength:Math.PI*2,thetaStart:0,thetaLength:Math.PI,radius:1},function(){this.build()},{build:function(){var e=this.heightSegments,t=this.widthSegments,r=this.attributes.position,i=this.attributes.texcoord0,n=this.attributes.normal,a=(t+1)*(e+1);r.init(a),i.init(a),n.init(a);var o=a>65535?Uint32Array:Uint16Array,s=this.indices=new o(t*e*6),l,u,f,h,d,c,v,T=this.radius,p=this.phiStart,m=this.phiLength,_=this.thetaStart,x=this.thetaLength,T=this.radius,g=[],E=[],S=0,C=1/T;for(v=0;v<=e;v++)for(c=0;c<=t;c++)h=c/t,d=v/e,l=-T*Math.cos(p+h*m)*Math.sin(_+d*x),u=T*Math.cos(_+d*x),f=T*Math.sin(p+h*m)*Math.sin(_+d*x),g[0]=l,g[1]=u,g[2]=f,E[0]=h,E[1]=d,r.set(S,g),i.set(S,E),g[0]*=C,g[1]*=C,g[2]*=C,n.set(S,g),S++;var A,N,H,R,U=t+1,V=0;for(v=0;v<e;v++)for(c=0;c<t;c++)N=v*U+c,A=v*U+c+1,R=(v+1)*U+c+1,H=(v+1)*U+c,s[V++]=A,s[V++]=N,s[V++]=R,s[V++]=N,s[V++]=H,s[V++]=R;this.boundingBox=new Ee,this.boundingBox.max.set(T,T,T),this.boundingBox.min.set(-T,-T,-T)}}),Vs=Xe.extend({castShadow:!1},{type:"AMBIENT_LIGHT",uniformTemplates:{ambientLightColor:{type:"3f",value:function(e){var t=e.color,r=e.intensity;return[t[0]*r,t[1]*r,t[2]*r]}}}}),Gs=Xe.extend({shadowBias:.001,shadowSlopeScale:2,shadowCascade:1,cascadeSplitLogFactor:.2},{type:"DIRECTIONAL_LIGHT",uniformTemplates:{directionalLightDirection:{type:"3f",value:function(e){return e.__dir=e.__dir||new b,e.__dir.copy(e.worldTransform.z).normalize().negate().array}},directionalLightColor:{type:"3f",value:function(e){var t=e.color,r=e.intensity;return[t[0]*r,t[1]*r,t[2]*r]}}},clone:function(){var e=Xe.prototype.clone.call(this);return e.shadowBias=this.shadowBias,e.shadowSlopeScale=this.shadowSlopeScale,e}}),ks=Xe.extend({range:100,castShadow:!1},{type:"POINT_LIGHT",uniformTemplates:{pointLightPosition:{type:"3f",value:function(e){return e.getWorldPosition().array}},pointLightRange:{type:"1f",value:function(e){return e.range}},pointLightColor:{type:"3f",value:function(e){var t=e.color,r=e.intensity;return[t[0]*r,t[1]*r,t[2]*r]}}},clone:function(){var e=Xe.prototype.clone.call(this);return e.range=this.range,e}}),Ws=Xe.extend({range:20,umbraAngle:30,penumbraAngle:45,falloffFactor:2,shadowBias:.001,shadowSlopeScale:2},{type:"SPOT_LIGHT",uniformTemplates:{spotLightPosition:{type:"3f",value:function(e){return e.getWorldPosition().array}},spotLightRange:{type:"1f",value:function(e){return e.range}},spotLightUmbraAngleCosine:{type:"1f",value:function(e){return Math.cos(e.umbraAngle*Math.PI/180)}},spotLightPenumbraAngleCosine:{type:"1f",value:function(e){return Math.cos(e.penumbraAngle*Math.PI/180)}},spotLightFalloffFactor:{type:"1f",value:function(e){return e.falloffFactor}},spotLightDirection:{type:"3f",value:function(e){return e.__dir=e.__dir||new b,e.__dir.copy(e.worldTransform.z).negate().array}},spotLightColor:{type:"3f",value:function(e){var t=e.color,r=e.intensity;return[t[0]*r,t[1]*r,t[2]*r]}}},clone:function(){var e=Xe.prototype.clone.call(this);return e.range=this.range,e.umbraAngle=this.umbraAngle,e.penumbraAngle=this.penumbraAngle,e.falloffFactor=this.falloffFactor,e.shadowBias=this.shadowBias,e.shadowSlopeScale=this.shadowSlopeScale,e}}),Z=function(e,t,r,i){e=e||0,t=t||0,r=r||0,i=i||0,this.array=M.fromValues(e,t,r,i),this._dirty=!0};Z.prototype={constructor:Z,add:function(e){return M.add(this.array,this.array,e.array),this._dirty=!0,this},set:function(e,t,r,i){return this.array[0]=e,this.array[1]=t,this.array[2]=r,this.array[3]=i,this._dirty=!0,this},setArray:function(e){return this.array[0]=e[0],this.array[1]=e[1],this.array[2]=e[2],this.array[3]=e[3],this._dirty=!0,this},clone:function(){return new Z(this.x,this.y,this.z,this.w)},copy:function(e){return M.copy(this.array,e.array),this._dirty=!0,this},dist:function(e){return M.dist(this.array,e.array)},distance:function(e){return M.distance(this.array,e.array)},div:function(e){return M.div(this.array,this.array,e.array),this._dirty=!0,this},divide:function(e){return M.divide(this.array,this.array,e.array),this._dirty=!0,this},dot:function(e){return M.dot(this.array,e.array)},len:function(){return M.len(this.array)},length:function(){return M.length(this.array)},lerp:function(e,t,r){return M.lerp(this.array,e.array,t.array,r),this._dirty=!0,this},min:function(e){return M.min(this.array,this.array,e.array),this._dirty=!0,this},max:function(e){return M.max(this.array,this.array,e.array),this._dirty=!0,this},mul:function(e){return M.mul(this.array,this.array,e.array),this._dirty=!0,this},multiply:function(e){return M.multiply(this.array,this.array,e.array),this._dirty=!0,this},negate:function(){return M.negate(this.array,this.array),this._dirty=!0,this},normalize:function(){return M.normalize(this.array,this.array),this._dirty=!0,this},random:function(e){return M.random(this.array,e),this._dirty=!0,this},scale:function(e){return M.scale(this.array,this.array,e),this._dirty=!0,this},scaleAndAdd:function(e,t){return M.scaleAndAdd(this.array,this.array,e.array,t),this._dirty=!0,this},sqrDist:function(e){return M.sqrDist(this.array,e.array)},squaredDistance:function(e){return M.squaredDistance(this.array,e.array)},sqrLen:function(){return M.sqrLen(this.array)},squaredLength:function(){return M.squaredLength(this.array)},sub:function(e){return M.sub(this.array,this.array,e.array),this._dirty=!0,this},subtract:function(e){return M.subtract(this.array,this.array,e.array),this._dirty=!0,this},transformMat4:function(e){return M.transformMat4(this.array,this.array,e.array),this._dirty=!0,this},transformQuat:function(e){return M.transformQuat(this.array,this.array,e.array),this._dirty=!0,this},toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};var tr=Object.defineProperty;if(tr){var Er=Z.prototype;tr(Er,"x",{get:function(){return this.array[0]},set:function(e){this.array[0]=e,this._dirty=!0}}),tr(Er,"y",{get:function(){return this.array[1]},set:function(e){this.array[1]=e,this._dirty=!0}}),tr(Er,"z",{get:function(){return this.array[2]},set:function(e){this.array[2]=e,this._dirty=!0}}),tr(Er,"w",{get:function(){return this.array[3]},set:function(e){this.array[3]=e,this._dirty=!0}})}Z.add=function(e,t,r){return M.add(e.array,t.array,r.array),e._dirty=!0,e};Z.set=function(e,t,r,i,n){M.set(e.array,t,r,i,n),e._dirty=!0};Z.copy=function(e,t){return M.copy(e.array,t.array),e._dirty=!0,e};Z.dist=function(e,t){return M.distance(e.array,t.array)};Z.distance=Z.dist;Z.div=function(e,t,r){return M.divide(e.array,t.array,r.array),e._dirty=!0,e};Z.divide=Z.div;Z.dot=function(e,t){return M.dot(e.array,t.array)};Z.len=function(e){return M.length(e.array)};Z.lerp=function(e,t,r,i){return M.lerp(e.array,t.array,r.array,i),e._dirty=!0,e};Z.min=function(e,t,r){return M.min(e.array,t.array,r.array),e._dirty=!0,e};Z.max=function(e,t,r){return M.max(e.array,t.array,r.array),e._dirty=!0,e};Z.mul=function(e,t,r){return M.multiply(e.array,t.array,r.array),e._dirty=!0,e};Z.multiply=Z.mul;Z.negate=function(e,t){return M.negate(e.array,t.array),e._dirty=!0,e};Z.normalize=function(e,t){return M.normalize(e.array,t.array),e._dirty=!0,e};Z.random=function(e,t){return M.random(e.array,t),e._dirty=!0,e};Z.scale=function(e,t,r){return M.scale(e.array,t.array,r),e._dirty=!0,e};Z.scaleAndAdd=function(e,t,r,i){return M.scaleAndAdd(e.array,t.array,r.array,i),e._dirty=!0,e};Z.sqrDist=function(e,t){return M.sqrDist(e.array,t.array)};Z.squaredDistance=Z.sqrDist;Z.sqrLen=function(e){return M.sqrLen(e.array)};Z.squaredLength=Z.sqrLen;Z.sub=function(e,t,r){return M.subtract(e.array,t.array,r.array),e._dirty=!0,e};Z.subtract=Z.sub;Z.transformMat4=function(e,t,r){return M.transformMat4(e.array,t.array,r.array),e._dirty=!0,e};Z.transformQuat=function(e,t,r){return M.transformQuat(e.array,t.array,r.array),e._dirty=!0,e};var Y={};Y.create=function(){var e=new Se(4);return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e};Y.clone=function(e){var t=new Se(4);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t};Y.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e};Y.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e};Y.transpose=function(e,t){if(e===t){var r=t[1];e[1]=t[2],e[2]=r}else e[0]=t[0],e[1]=t[2],e[2]=t[1],e[3]=t[3];return e};Y.invert=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=r*a-n*i;return o?(o=1/o,e[0]=a*o,e[1]=-i*o,e[2]=-n*o,e[3]=r*o,e):null};Y.adjoint=function(e,t){var r=t[0];return e[0]=t[3],e[1]=-t[1],e[2]=-t[2],e[3]=r,e};Y.determinant=function(e){return e[0]*e[3]-e[2]*e[1]};Y.multiply=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=r[0],l=r[1],u=r[2],f=r[3];return e[0]=i*s+a*l,e[1]=n*s+o*l,e[2]=i*u+a*f,e[3]=n*u+o*f,e};Y.mul=Y.multiply;Y.rotate=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=Math.sin(r),l=Math.cos(r);return e[0]=i*l+a*s,e[1]=n*l+o*s,e[2]=i*-s+a*l,e[3]=n*-s+o*l,e};Y.scale=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=r[0],l=r[1];return e[0]=i*s,e[1]=n*s,e[2]=a*l,e[3]=o*l,e};Y.frob=function(e){return Math.sqrt(Math.pow(e[0],2)+Math.pow(e[1],2)+Math.pow(e[2],2)+Math.pow(e[3],2))};Y.LDU=function(e,t,r,i){return e[2]=i[2]/i[0],r[0]=i[0],r[1]=i[1],r[3]=i[3]-e[2]*r[1],[e,t,r]};var De=function(){this.array=Y.create(),this._dirty=!0};De.prototype={constructor:De,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},clone:function(){return new De().copy(this)},copy:function(e){return Y.copy(this.array,e.array),this._dirty=!0,this},adjoint:function(){return Y.adjoint(this.array,this.array),this._dirty=!0,this},determinant:function(){return Y.determinant(this.array)},identity:function(){return Y.identity(this.array),this._dirty=!0,this},invert:function(){return Y.invert(this.array,this.array),this._dirty=!0,this},mul:function(e){return Y.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return Y.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return Y.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return Y.multiply(this.array,e.array,this.array),this._dirty=!0,this},rotate:function(e){return Y.rotate(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return Y.scale(this.array,this.array,e.array),this._dirty=!0,this},transpose:function(){return Y.transpose(this.array,this.array),this._dirty=!0,this},toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};De.adjoint=function(e,t){return Y.adjoint(e.array,t.array),e._dirty=!0,e};De.copy=function(e,t){return Y.copy(e.array,t.array),e._dirty=!0,e};De.determinant=function(e){return Y.determinant(e.array)};De.identity=function(e){return Y.identity(e.array),e._dirty=!0,e};De.invert=function(e,t){return Y.invert(e.array,t.array),e._dirty=!0,e};De.mul=function(e,t,r){return Y.mul(e.array,t.array,r.array),e._dirty=!0,e};De.multiply=De.mul;De.rotate=function(e,t,r){return Y.rotate(e.array,t.array,r),e._dirty=!0,e};De.scale=function(e,t,r){return Y.scale(e.array,t.array,r.array),e._dirty=!0,e};De.transpose=function(e,t){return Y.transpose(e.array,t.array),e._dirty=!0,e};var $={};$.create=function(){var e=new Se(6);return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e[4]=0,e[5]=0,e};$.clone=function(e){var t=new Se(6);return t[0]=e[0],t[1]=e[1],t[2]=e[2],t[3]=e[3],t[4]=e[4],t[5]=e[5],t};$.copy=function(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4],e[5]=t[5],e};$.identity=function(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e[4]=0,e[5]=0,e};$.invert=function(e,t){var r=t[0],i=t[1],n=t[2],a=t[3],o=t[4],s=t[5],l=r*a-i*n;return l?(l=1/l,e[0]=a*l,e[1]=-i*l,e[2]=-n*l,e[3]=r*l,e[4]=(n*s-a*o)*l,e[5]=(i*o-r*s)*l,e):null};$.determinant=function(e){return e[0]*e[3]-e[1]*e[2]};$.multiply=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=r[0],f=r[1],h=r[2],d=r[3],c=r[4],v=r[5];return e[0]=i*u+a*f,e[1]=n*u+o*f,e[2]=i*h+a*d,e[3]=n*h+o*d,e[4]=i*c+a*v+s,e[5]=n*c+o*v+l,e};$.mul=$.multiply;$.rotate=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=Math.sin(r),f=Math.cos(r);return e[0]=i*f+a*u,e[1]=n*f+o*u,e[2]=i*-u+a*f,e[3]=n*-u+o*f,e[4]=s,e[5]=l,e};$.scale=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=r[0],f=r[1];return e[0]=i*u,e[1]=n*u,e[2]=a*f,e[3]=o*f,e[4]=s,e[5]=l,e};$.translate=function(e,t,r){var i=t[0],n=t[1],a=t[2],o=t[3],s=t[4],l=t[5],u=r[0],f=r[1];return e[0]=i,e[1]=n,e[2]=a,e[3]=o,e[4]=i*u+a*f+s,e[5]=n*u+o*f+l,e};$.frob=function(e){return Math.sqrt(Math.pow(e[0],2)+Math.pow(e[1],2)+Math.pow(e[2],2)+Math.pow(e[3],2)+Math.pow(e[4],2)+Math.pow(e[5],2)+1)};var Ie=function(){this.array=$.create(),this._dirty=!0};Ie.prototype={constructor:Ie,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},clone:function(){return new Ie().copy(this)},copy:function(e){return $.copy(this.array,e.array),this._dirty=!0,this},determinant:function(){return $.determinant(this.array)},identity:function(){return $.identity(this.array),this._dirty=!0,this},invert:function(){return $.invert(this.array,this.array),this._dirty=!0,this},mul:function(e){return $.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return $.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return $.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return $.multiply(this.array,e.array,this.array),this._dirty=!0,this},rotate:function(e){return $.rotate(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return $.scale(this.array,this.array,e.array),this._dirty=!0,this},translate:function(e){return $.translate(this.array,this.array,e.array),this._dirty=!0,this},toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};Ie.copy=function(e,t){return $.copy(e.array,t.array),e._dirty=!0,e};Ie.determinant=function(e){return $.determinant(e.array)};Ie.identity=function(e){return $.identity(e.array),e._dirty=!0,e};Ie.invert=function(e,t){return $.invert(e.array,t.array),e._dirty=!0,e};Ie.mul=function(e,t,r){return $.mul(e.array,t.array,r.array),e._dirty=!0,e};Ie.multiply=Ie.mul;Ie.rotate=function(e,t,r){return $.rotate(e.array,t.array,r),e._dirty=!0,e};Ie.scale=function(e,t,r){return $.scale(e.array,t.array,r.array),e._dirty=!0,e};Ie.translate=function(e,t,r){return $.translate(e.array,t.array,r.array),e._dirty=!0,e};var pe=function(){this.array=k.create(),this._dirty=!0};pe.prototype={constructor:pe,setArray:function(e){for(var t=0;t<this.array.length;t++)this.array[t]=e[t];return this._dirty=!0,this},adjoint:function(){return k.adjoint(this.array,this.array),this._dirty=!0,this},clone:function(){return new pe().copy(this)},copy:function(e){return k.copy(this.array,e.array),this._dirty=!0,this},determinant:function(){return k.determinant(this.array)},fromMat2d:function(e){return k.fromMat2d(this.array,e.array),this._dirty=!0,this},fromMat4:function(e){return k.fromMat4(this.array,e.array),this._dirty=!0,this},fromQuat:function(e){return k.fromQuat(this.array,e.array),this._dirty=!0,this},identity:function(){return k.identity(this.array),this._dirty=!0,this},invert:function(){return k.invert(this.array,this.array),this._dirty=!0,this},mul:function(e){return k.mul(this.array,this.array,e.array),this._dirty=!0,this},mulLeft:function(e){return k.mul(this.array,e.array,this.array),this._dirty=!0,this},multiply:function(e){return k.multiply(this.array,this.array,e.array),this._dirty=!0,this},multiplyLeft:function(e){return k.multiply(this.array,e.array,this.array),this._dirty=!0,this},rotate:function(e){return k.rotate(this.array,this.array,e),this._dirty=!0,this},scale:function(e){return k.scale(this.array,this.array,e.array),this._dirty=!0,this},translate:function(e){return k.translate(this.array,this.array,e.array),this._dirty=!0,this},normalFromMat4:function(e){return k.normalFromMat4(this.array,e.array),this._dirty=!0,this},transpose:function(){return k.transpose(this.array,this.array),this._dirty=!0,this},toString:function(){return"["+Array.prototype.join.call(this.array,",")+"]"},toArray:function(){return Array.prototype.slice.call(this.array)}};pe.adjoint=function(e,t){return k.adjoint(e.array,t.array),e._dirty=!0,e};pe.copy=function(e,t){return k.copy(e.array,t.array),e._dirty=!0,e};pe.determinant=function(e){return k.determinant(e.array)};pe.identity=function(e){return k.identity(e.array),e._dirty=!0,e};pe.invert=function(e,t){return k.invert(e.array,t.array),e};pe.mul=function(e,t,r){return k.mul(e.array,t.array,r.array),e._dirty=!0,e};pe.multiply=pe.mul;pe.fromMat2d=function(e,t){return k.fromMat2d(e.array,t.array),e._dirty=!0,e};pe.fromMat4=function(e,t){return k.fromMat4(e.array,t.array),e._dirty=!0,e};pe.fromQuat=function(e,t){return k.fromQuat(e.array,t.array),e._dirty=!0,e};pe.normalFromMat4=function(e,t){return k.normalFromMat4(e.array,t.array),e._dirty=!0,e};pe.rotate=function(e,t,r){return k.rotate(e.array,t.array,r),e._dirty=!0,e};pe.scale=function(e,t,r){return k.scale(e.array,t.array,r.array),e._dirty=!0,e};pe.transpose=function(e,t){return k.transpose(e.array,t.array),e._dirty=!0,e};pe.translate=function(e,t,r){return k.translate(e.array,t.array,r.array),e._dirty=!0,e};var Xs={_animators:null,getAnimators:function(){return this._animators=this._animators||[],this._animators},animate:function(e,t){this._animators=this._animators||[];var r=this,i;if(e){for(var n=e.split("."),a=r,o=0,s=n.length;o<s;o++)a&&(a=a[n[o]]);a&&(i=a)}else i=r;if(i==null)throw new Error("Target "+e+" not exists");var l=this._animators,u=new ja(i,t),f=this;return u.during(function(){f.__zr&&f.__zr.refresh()}).done(function(){var h=l.indexOf(u);h>=0&&l.splice(h,1)}),l.push(u),this.__zr&&this.__zr.animation.addAnimator(u),u},stopAnimation:function(e){this._animators=this._animators||[];for(var t=this._animators,r=t.length,i=0;i<r;i++)t[i].stop(e);return t.length=0,this},addAnimatorsToZr:function(e){if(this._animators)for(var t=0;t<this._animators.length;t++)e.animation.addAnimator(this._animators[t])},removeAnimatorsFromZr:function(e){if(this._animators)for(var t=0;t<this._animators.length;t++)e.animation.removeAnimator(this._animators[t])}};const qs=`
@export clay.util.rand
highp float rand(vec2 uv) {
 const highp float a = 12.9898, b = 78.233, c = 43758.5453;
 highp float dt = dot(uv.xy, vec2(a,b)), sn = mod(dt, 3.141592653589793);
 return fract(sin(sn) * c);
}
@end
@export clay.util.calculate_attenuation
uniform float attenuationFactor : 5.0;
float lightAttenuation(float dist, float range)
{
 float attenuation = 1.0;
 attenuation = dist*dist/(range*range+1.0);
 float att_s = attenuationFactor;
 attenuation = 1.0/(attenuation*att_s+1.0);
 att_s = 1.0/(att_s+1.0);
 attenuation = attenuation - att_s;
 attenuation /= 1.0 - att_s;
 return clamp(attenuation, 0.0, 1.0);
}
@end
@export clay.util.edge_factor
#ifdef SUPPORT_STANDARD_DERIVATIVES
float edgeFactor(float width)
{
 vec3 d = fwidth(v_Barycentric);
 vec3 a3 = smoothstep(vec3(0.0), d * width, v_Barycentric);
 return min(min(a3.x, a3.y), a3.z);
}
#else
float edgeFactor(float width)
{
 return 1.0;
}
#endif
@end
@export clay.util.encode_float
vec4 encodeFloat(const in float depth)
{
 const vec4 bitShifts = vec4(256.0*256.0*256.0, 256.0*256.0, 256.0, 1.0);
 const vec4 bit_mask = vec4(0.0, 1.0/256.0, 1.0/256.0, 1.0/256.0);
 vec4 res = fract(depth * bitShifts);
 res -= res.xxyz * bit_mask;
 return res;
}
@end
@export clay.util.decode_float
float decodeFloat(const in vec4 color)
{
 const vec4 bitShifts = vec4(1.0/(256.0*256.0*256.0), 1.0/(256.0*256.0), 1.0/256.0, 1.0);
 return dot(color, bitShifts);
}
@end
@export clay.util.float
@import clay.util.encode_float
@import clay.util.decode_float
@end
@export clay.util.rgbm_decode
vec3 RGBMDecode(vec4 rgbm, float range) {
 return range * rgbm.rgb * rgbm.a;
}
@end
@export clay.util.rgbm_encode
vec4 RGBMEncode(vec3 color, float range) {
 if (dot(color, color) == 0.0) {
 return vec4(0.0);
 }
 vec4 rgbm;
 color /= range;
 rgbm.a = clamp(max(max(color.r, color.g), max(color.b, 1e-6)), 0.0, 1.0);
 rgbm.a = ceil(rgbm.a * 255.0) / 255.0;
 rgbm.rgb = color / rgbm.a;
 return rgbm;
}
@end
@export clay.util.rgbm
@import clay.util.rgbm_decode
@import clay.util.rgbm_encode
vec4 decodeHDR(vec4 color)
{
#if defined(RGBM_DECODE) || defined(RGBM)
 return vec4(RGBMDecode(color, 8.12), 1.0);
#else
 return color;
#endif
}
vec4 encodeHDR(vec4 color)
{
#if defined(RGBM_ENCODE) || defined(RGBM)
 return RGBMEncode(color.xyz, 8.12);
#else
 return color;
#endif
}
@end
@export clay.util.srgb
vec4 sRGBToLinear(in vec4 value) {
 return vec4(mix(pow(value.rgb * 0.9478672986 + vec3(0.0521327014), vec3(2.4)), value.rgb * 0.0773993808, vec3(lessThanEqual(value.rgb, vec3(0.04045)))), value.w);
}
vec4 linearTosRGB(in vec4 value) {
 return vec4(mix(pow(value.rgb, vec3(0.41666)) * 1.055 - vec3(0.055), value.rgb * 12.92, vec3(lessThanEqual(value.rgb, vec3(0.0031308)))), value.w);
}
@end
@export clay.chunk.skinning_header
#ifdef SKINNING
attribute vec3 weight : WEIGHT;
attribute vec4 joint : JOINT;
#ifdef USE_SKIN_MATRICES_TEXTURE
uniform sampler2D skinMatricesTexture : ignore;
uniform float skinMatricesTextureSize: ignore;
mat4 getSkinMatrix(sampler2D tex, float idx) {
 float j = idx * 4.0;
 float x = mod(j, skinMatricesTextureSize);
 float y = floor(j / skinMatricesTextureSize) + 0.5;
 vec2 scale = vec2(skinMatricesTextureSize);
 return mat4(
 texture2D(tex, vec2(x + 0.5, y) / scale),
 texture2D(tex, vec2(x + 1.5, y) / scale),
 texture2D(tex, vec2(x + 2.5, y) / scale),
 texture2D(tex, vec2(x + 3.5, y) / scale)
 );
}
mat4 getSkinMatrix(float idx) {
 return getSkinMatrix(skinMatricesTexture, idx);
}
#else
uniform mat4 skinMatrix[JOINT_COUNT] : SKIN_MATRIX;
mat4 getSkinMatrix(float idx) {
 return skinMatrix[int(idx)];
}
#endif
#endif
@end
@export clay.chunk.skin_matrix
mat4 skinMatrixWS = getSkinMatrix(joint.x) * weight.x;
if (weight.y > 1e-4)
{
 skinMatrixWS += getSkinMatrix(joint.y) * weight.y;
}
if (weight.z > 1e-4)
{
 skinMatrixWS += getSkinMatrix(joint.z) * weight.z;
}
float weightW = 1.0-weight.x-weight.y-weight.z;
if (weightW > 1e-4)
{
 skinMatrixWS += getSkinMatrix(joint.w) * weightW;
}
@end
@export clay.chunk.instancing_header
#ifdef INSTANCING
attribute vec4 instanceMat1;
attribute vec4 instanceMat2;
attribute vec4 instanceMat3;
#endif
@end
@export clay.chunk.instancing_matrix
mat4 instanceMat = mat4(
 vec4(instanceMat1.xyz, 0.0),
 vec4(instanceMat2.xyz, 0.0),
 vec4(instanceMat3.xyz, 0.0),
 vec4(instanceMat1.w, instanceMat2.w, instanceMat3.w, 1.0)
);
@end
@export clay.util.parallax_correct
vec3 parallaxCorrect(in vec3 dir, in vec3 pos, in vec3 boxMin, in vec3 boxMax) {
 vec3 first = (boxMax - pos) / dir;
 vec3 second = (boxMin - pos) / dir;
 vec3 further = max(first, second);
 float dist = min(further.x, min(further.y, further.z));
 vec3 fixedPos = pos + dir * dist;
 vec3 boxCenter = (boxMax + boxMin) * 0.5;
 return normalize(fixedPos - boxCenter);
}
@end
@export clay.util.clamp_sample
vec4 clampSample(const in sampler2D texture, const in vec2 coord)
{
#ifdef STEREO
 float eye = step(0.5, coord.x) * 0.5;
 vec2 coordClamped = clamp(coord, vec2(eye, 0.0), vec2(0.5 + eye, 1.0));
#else
 vec2 coordClamped = clamp(coord, vec2(0.0), vec2(1.0));
#endif
 return texture2D(texture, coordClamped);
}
@end
@export clay.util.ACES
vec3 ACESToneMapping(vec3 color)
{
 const float A = 2.51;
 const float B = 0.03;
 const float C = 2.43;
 const float D = 0.59;
 const float E = 0.14;
 return (color * (A * color + B)) / (color * (C * color + D) + E);
}
@end`,js=`
@export ecgl.common.transformUniforms
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform mat4 worldInverseTranspose : WORLDINVERSETRANSPOSE;
uniform mat4 world : WORLD;
@end

@export ecgl.common.attributes
attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;
attribute vec3 normal : NORMAL;
@end

@export ecgl.common.uv.header
uniform vec2 uvRepeat : [1.0, 1.0];
uniform vec2 uvOffset : [0.0, 0.0];
uniform vec2 detailUvRepeat : [1.0, 1.0];
uniform vec2 detailUvOffset : [0.0, 0.0];

varying vec2 v_Texcoord;
varying vec2 v_DetailTexcoord;
@end

@export ecgl.common.uv.main
v_Texcoord = texcoord * uvRepeat + uvOffset;
v_DetailTexcoord = texcoord * detailUvRepeat + detailUvOffset;
@end

@export ecgl.common.uv.fragmentHeader
varying vec2 v_Texcoord;
varying vec2 v_DetailTexcoord;
@end


@export ecgl.common.albedo.main

 vec4 albedoTexel = vec4(1.0);
#ifdef DIFFUSEMAP_ENABLED
 albedoTexel = texture2D(diffuseMap, v_Texcoord);
 #ifdef SRGB_DECODE
 albedoTexel = sRGBToLinear(albedoTexel);
 #endif
#endif

#ifdef DETAILMAP_ENABLED
 vec4 detailTexel = texture2D(detailMap, v_DetailTexcoord);
 #ifdef SRGB_DECODE
 detailTexel = sRGBToLinear(detailTexel);
 #endif
 albedoTexel.rgb = mix(albedoTexel.rgb, detailTexel.rgb, detailTexel.a);
 albedoTexel.a = detailTexel.a + (1.0 - detailTexel.a) * albedoTexel.a;
#endif

@end

@export ecgl.common.wireframe.vertexHeader

#ifdef WIREFRAME_QUAD
attribute vec4 barycentric;
varying vec4 v_Barycentric;
#elif defined(WIREFRAME_TRIANGLE)
attribute vec3 barycentric;
varying vec3 v_Barycentric;
#endif

@end

@export ecgl.common.wireframe.vertexMain

#if defined(WIREFRAME_QUAD) || defined(WIREFRAME_TRIANGLE)
 v_Barycentric = barycentric;
#endif

@end


@export ecgl.common.wireframe.fragmentHeader

uniform float wireframeLineWidth : 1;
uniform vec4 wireframeLineColor: [0, 0, 0, 0.5];

#ifdef WIREFRAME_QUAD
varying vec4 v_Barycentric;
float edgeFactor () {
 vec4 d = fwidth(v_Barycentric);
 vec4 a4 = smoothstep(vec4(0.0), d * wireframeLineWidth, v_Barycentric);
 return min(min(min(a4.x, a4.y), a4.z), a4.w);
}
#elif defined(WIREFRAME_TRIANGLE)
varying vec3 v_Barycentric;
float edgeFactor () {
 vec3 d = fwidth(v_Barycentric);
 vec3 a3 = smoothstep(vec3(0.0), d * wireframeLineWidth, v_Barycentric);
 return min(min(a3.x, a3.y), a3.z);
}
#endif

@end


@export ecgl.common.wireframe.fragmentMain

#if defined(WIREFRAME_QUAD) || defined(WIREFRAME_TRIANGLE)
 if (wireframeLineWidth > 0.) {
 vec4 lineColor = wireframeLineColor;
#ifdef SRGB_DECODE
 lineColor = sRGBToLinear(lineColor);
#endif

 gl_FragColor.rgb = mix(gl_FragColor.rgb, lineColor.rgb, (1.0 - edgeFactor()) * lineColor.a);
 }
#endif
@end




@export ecgl.common.bumpMap.header

#ifdef BUMPMAP_ENABLED
uniform sampler2D bumpMap;
uniform float bumpScale : 1.0;


vec3 bumpNormal(vec3 surfPos, vec3 surfNormal, vec3 baseNormal)
{
 vec2 dSTdx = dFdx(v_Texcoord);
 vec2 dSTdy = dFdy(v_Texcoord);

 float Hll = bumpScale * texture2D(bumpMap, v_Texcoord).x;
 float dHx = bumpScale * texture2D(bumpMap, v_Texcoord + dSTdx).x - Hll;
 float dHy = bumpScale * texture2D(bumpMap, v_Texcoord + dSTdy).x - Hll;

 vec3 vSigmaX = dFdx(surfPos);
 vec3 vSigmaY = dFdy(surfPos);
 vec3 vN = surfNormal;

 vec3 R1 = cross(vSigmaY, vN);
 vec3 R2 = cross(vN, vSigmaX);

 float fDet = dot(vSigmaX, R1);

 vec3 vGrad = sign(fDet) * (dHx * R1 + dHy * R2);
 return normalize(abs(fDet) * baseNormal - vGrad);

}
#endif

@end

@export ecgl.common.normalMap.vertexHeader

#ifdef NORMALMAP_ENABLED
attribute vec4 tangent : TANGENT;
varying vec3 v_Tangent;
varying vec3 v_Bitangent;
#endif

@end

@export ecgl.common.normalMap.vertexMain

#ifdef NORMALMAP_ENABLED
 if (dot(tangent, tangent) > 0.0) {
 v_Tangent = normalize((worldInverseTranspose * vec4(tangent.xyz, 0.0)).xyz);
 v_Bitangent = normalize(cross(v_Normal, v_Tangent) * tangent.w);
 }
#endif

@end


@export ecgl.common.normalMap.fragmentHeader

#ifdef NORMALMAP_ENABLED
uniform sampler2D normalMap;
varying vec3 v_Tangent;
varying vec3 v_Bitangent;
#endif

@end

@export ecgl.common.normalMap.fragmentMain
#ifdef NORMALMAP_ENABLED
 if (dot(v_Tangent, v_Tangent) > 0.0) {
 vec3 normalTexel = texture2D(normalMap, v_DetailTexcoord).xyz;
 if (dot(normalTexel, normalTexel) > 0.0) { N = normalTexel * 2.0 - 1.0;
 mat3 tbn = mat3(v_Tangent, v_Bitangent, v_Normal);
 N = normalize(tbn * N);
 }
 }
#endif
@end



@export ecgl.common.vertexAnimation.header

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
attribute vec3 prevNormal;
uniform float percent;
#endif

@end

@export ecgl.common.vertexAnimation.main

#ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
 vec3 norm = mix(prevNormal, normal, percent);
#else
 vec3 pos = position;
 vec3 norm = normal;
#endif

@end


@export ecgl.common.ssaoMap.header
#ifdef SSAOMAP_ENABLED
uniform sampler2D ssaoMap;
uniform vec4 viewport : VIEWPORT;
#endif
@end

@export ecgl.common.ssaoMap.main
 float ao = 1.0;
#ifdef SSAOMAP_ENABLED
 ao = texture2D(ssaoMap, (gl_FragCoord.xy - viewport.xy) / viewport.zw).r;
#endif
@end




@export ecgl.common.diffuseLayer.header

#if (LAYER_DIFFUSEMAP_COUNT > 0)
uniform float layerDiffuseIntensity[LAYER_DIFFUSEMAP_COUNT];
uniform sampler2D layerDiffuseMap[LAYER_DIFFUSEMAP_COUNT];
#endif

@end

@export ecgl.common.emissiveLayer.header

#if (LAYER_EMISSIVEMAP_COUNT > 0)
uniform float layerEmissionIntensity[LAYER_EMISSIVEMAP_COUNT];
uniform sampler2D layerEmissiveMap[LAYER_EMISSIVEMAP_COUNT];
#endif

@end

@export ecgl.common.layers.header
@import ecgl.common.diffuseLayer.header
@import ecgl.common.emissiveLayer.header
@end

@export ecgl.common.diffuseLayer.main

#if (LAYER_DIFFUSEMAP_COUNT > 0)
 for (int _idx_ = 0; _idx_ < LAYER_DIFFUSEMAP_COUNT; _idx_++) {{
 float intensity = layerDiffuseIntensity[_idx_];
 vec4 texel2 = texture2D(layerDiffuseMap[_idx_], v_Texcoord);
 #ifdef SRGB_DECODE
 texel2 = sRGBToLinear(texel2);
 #endif
 albedoTexel.rgb = mix(albedoTexel.rgb, texel2.rgb * intensity, texel2.a);
 albedoTexel.a = texel2.a + (1.0 - texel2.a) * albedoTexel.a;
 }}
#endif

@end

@export ecgl.common.emissiveLayer.main

#if (LAYER_EMISSIVEMAP_COUNT > 0)
 for (int _idx_ = 0; _idx_ < LAYER_EMISSIVEMAP_COUNT; _idx_++)
 {{
 vec4 texel2 = texture2D(layerEmissiveMap[_idx_], v_Texcoord) * layerEmissionIntensity[_idx_];
 #ifdef SRGB_DECODE
 texel2 = sRGBToLinear(texel2);
 #endif
 float intensity = layerEmissionIntensity[_idx_];
 gl_FragColor.rgb += texel2.rgb * texel2.a * intensity;
 }}
#endif

@end
`,Zs=`@export ecgl.color.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

@import ecgl.common.uv.header

attribute vec2 texcoord : TEXCOORD_0;
attribute vec3 position: POSITION;

@import ecgl.common.wireframe.vertexHeader

#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
uniform float percent : 1.0;
#endif

#ifdef ATMOSPHERE_ENABLED
attribute vec3 normal: NORMAL;
uniform mat4 worldInverseTranspose : WORLDINVERSETRANSPOSE;
varying vec3 v_Normal;
#endif

void main()
{
#ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
#else
 vec3 pos = position;
#endif

 gl_Position = worldViewProjection * vec4(pos, 1.0);

 @import ecgl.common.uv.main

#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif

#ifdef ATMOSPHERE_ENABLED
 v_Normal = normalize((worldInverseTranspose * vec4(normal, 0.0)).xyz);
#endif

 @import ecgl.common.wireframe.vertexMain

}

@end

@export ecgl.color.fragment

#define LAYER_DIFFUSEMAP_COUNT 0
#define LAYER_EMISSIVEMAP_COUNT 0

uniform sampler2D diffuseMap;
uniform sampler2D detailMap;

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

#ifdef ATMOSPHERE_ENABLED
uniform mat4 viewTranspose: VIEWTRANSPOSE;
uniform vec3 glowColor;
uniform float glowPower;
varying vec3 v_Normal;
#endif

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif

@import ecgl.common.layers.header

@import ecgl.common.uv.fragmentHeader

@import ecgl.common.wireframe.fragmentHeader

@import clay.util.srgb

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color);
#else
 gl_FragColor = color;
#endif

#ifdef VERTEX_COLOR
 gl_FragColor *= v_Color;
#endif

 @import ecgl.common.albedo.main

 @import ecgl.common.diffuseLayer.main

 gl_FragColor *= albedoTexel;

#ifdef ATMOSPHERE_ENABLED
 float atmoIntensity = pow(1.0 - dot(v_Normal, (viewTranspose * vec4(0.0, 0.0, 1.0, 0.0)).xyz), glowPower);
 gl_FragColor.rgb += glowColor * atmoIntensity;
#endif

 @import ecgl.common.emissiveLayer.main

 @import ecgl.common.wireframe.fragmentMain

}
@end`,Ys=`/**
 * http: */

@export ecgl.lambert.vertex

@import ecgl.common.transformUniforms

@import ecgl.common.uv.header


@import ecgl.common.attributes

@import ecgl.common.wireframe.vertexHeader

#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif


@import ecgl.common.vertexAnimation.header


varying vec3 v_Normal;
varying vec3 v_WorldPosition;

void main()
{
 @import ecgl.common.uv.main

 @import ecgl.common.vertexAnimation.main


 gl_Position = worldViewProjection * vec4(pos, 1.0);

 v_Normal = normalize((worldInverseTranspose * vec4(norm, 0.0)).xyz);
 v_WorldPosition = (world * vec4(pos, 1.0)).xyz;

#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif

 @import ecgl.common.wireframe.vertexMain
}

@end


@export ecgl.lambert.fragment

#define LAYER_DIFFUSEMAP_COUNT 0
#define LAYER_EMISSIVEMAP_COUNT 0

#define NORMAL_UP_AXIS 1
#define NORMAL_FRONT_AXIS 2

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform sampler2D diffuseMap;
uniform sampler2D detailMap;

@import ecgl.common.layers.header

uniform float emissionIntensity: 1.0;

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

uniform mat4 viewInverse : VIEWINVERSE;

#ifdef ATMOSPHERE_ENABLED
uniform mat4 viewTranspose: VIEWTRANSPOSE;
uniform vec3 glowColor;
uniform float glowPower;
#endif

#ifdef AMBIENT_LIGHT_COUNT
@import clay.header.ambient_light
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
@import clay.header.ambient_sh_light
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
@import clay.header.directional_light
#endif

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif


@import ecgl.common.ssaoMap.header

@import ecgl.common.bumpMap.header

@import clay.util.srgb

@import ecgl.common.wireframe.fragmentHeader

@import clay.plugin.compute_shadow_map

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color);
#else
 gl_FragColor = color;
#endif

#ifdef VERTEX_COLOR
 #ifdef SRGB_DECODE
 gl_FragColor *= sRGBToLinear(v_Color);
 #else
 gl_FragColor *= v_Color;
 #endif
#endif

 @import ecgl.common.albedo.main

 @import ecgl.common.diffuseLayer.main

 gl_FragColor *= albedoTexel;

 vec3 N = v_Normal;
#ifdef DOUBLE_SIDED
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);

 if (dot(N, V) < 0.0) {
 N = -N;
 }
#endif

 float ambientFactor = 1.0;

#ifdef BUMPMAP_ENABLED
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 ambientFactor = dot(v_Normal, N);
#endif

 vec3 N2 = vec3(N.x, N[NORMAL_UP_AXIS], N[NORMAL_FRONT_AXIS]);

 vec3 diffuseColor = vec3(0.0, 0.0, 0.0);

 @import ecgl.common.ssaoMap.main

#ifdef AMBIENT_LIGHT_COUNT
 for(int i = 0; i < AMBIENT_LIGHT_COUNT; i++)
 {
 diffuseColor += ambientLightColor[i] * ambientFactor * ao;
 }
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_SH_LIGHT_COUNT; _idx_++)
 {{
 diffuseColor += calcAmbientSHLight(_idx_, N2) * ambientSHLightColor[_idx_] * ao;
 }}
#endif
#ifdef DIRECTIONAL_LIGHT_COUNT
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 float shadowContribsDir[DIRECTIONAL_LIGHT_COUNT];
 if(shadowEnabled)
 {
 computeShadowOfDirectionalLights(v_WorldPosition, shadowContribsDir);
 }
#endif
 for(int i = 0; i < DIRECTIONAL_LIGHT_COUNT; i++)
 {
 vec3 lightDirection = -directionalLightDirection[i];
 vec3 lightColor = directionalLightColor[i];

 float shadowContrib = 1.0;
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 if (shadowEnabled)
 {
 shadowContrib = shadowContribsDir[i];
 }
#endif

 float ndl = dot(N, normalize(lightDirection)) * shadowContrib;

 diffuseColor += lightColor * clamp(ndl, 0.0, 1.0);
 }
#endif

 gl_FragColor.rgb *= diffuseColor;

#ifdef ATMOSPHERE_ENABLED
 float atmoIntensity = pow(1.0 - dot(v_Normal, (viewTranspose * vec4(0.0, 0.0, 1.0, 0.0)).xyz), glowPower);
 gl_FragColor.rgb += glowColor * atmoIntensity;
#endif

 @import ecgl.common.emissiveLayer.main

 @import ecgl.common.wireframe.fragmentMain
}

@end`,Ks=`@export ecgl.realistic.vertex

@import ecgl.common.transformUniforms

@import ecgl.common.uv.header

@import ecgl.common.attributes


@import ecgl.common.wireframe.vertexHeader

#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif

#ifdef NORMALMAP_ENABLED
attribute vec4 tangent : TANGENT;
varying vec3 v_Tangent;
varying vec3 v_Bitangent;
#endif

@import ecgl.common.vertexAnimation.header

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

void main()
{

 @import ecgl.common.uv.main

 @import ecgl.common.vertexAnimation.main

 gl_Position = worldViewProjection * vec4(pos, 1.0);

 v_Normal = normalize((worldInverseTranspose * vec4(norm, 0.0)).xyz);
 v_WorldPosition = (world * vec4(pos, 1.0)).xyz;

#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif

#ifdef NORMALMAP_ENABLED
 v_Tangent = normalize((worldInverseTranspose * vec4(tangent.xyz, 0.0)).xyz);
 v_Bitangent = normalize(cross(v_Normal, v_Tangent) * tangent.w);
#endif

 @import ecgl.common.wireframe.vertexMain

}

@end



@export ecgl.realistic.fragment

#define LAYER_DIFFUSEMAP_COUNT 0
#define LAYER_EMISSIVEMAP_COUNT 0
#define PI 3.14159265358979
#define ROUGHNESS_CHANEL 0
#define METALNESS_CHANEL 1

#define NORMAL_UP_AXIS 1
#define NORMAL_FRONT_AXIS 2

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform sampler2D diffuseMap;

uniform sampler2D detailMap;
uniform sampler2D metalnessMap;
uniform sampler2D roughnessMap;

@import ecgl.common.layers.header

uniform float emissionIntensity: 1.0;

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

uniform float metalness : 0.0;
uniform float roughness : 0.5;

uniform mat4 viewInverse : VIEWINVERSE;

#ifdef ATMOSPHERE_ENABLED
uniform mat4 viewTranspose: VIEWTRANSPOSE;
uniform vec3 glowColor;
uniform float glowPower;
#endif

#ifdef AMBIENT_LIGHT_COUNT
@import clay.header.ambient_light
#endif

#ifdef AMBIENT_SH_LIGHT_COUNT
@import clay.header.ambient_sh_light
#endif

#ifdef AMBIENT_CUBEMAP_LIGHT_COUNT
@import clay.header.ambient_cubemap_light
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
@import clay.header.directional_light
#endif

@import ecgl.common.normalMap.fragmentHeader

@import ecgl.common.ssaoMap.header

@import ecgl.common.bumpMap.header

@import clay.util.srgb

@import clay.util.rgbm

@import ecgl.common.wireframe.fragmentHeader

@import clay.plugin.compute_shadow_map

vec3 F_Schlick(float ndv, vec3 spec) {
 return spec + (1.0 - spec) * pow(1.0 - ndv, 5.0);
}

float D_Phong(float g, float ndh) {
 float a = pow(8192.0, g);
 return (a + 2.0) / 8.0 * pow(ndh, a);
}

void main()
{
 vec4 albedoColor = color;

 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);
#ifdef VERTEX_COLOR
 #ifdef SRGB_DECODE
 albedoColor *= sRGBToLinear(v_Color);
 #else
 albedoColor *= v_Color;
 #endif
#endif

 @import ecgl.common.albedo.main

 @import ecgl.common.diffuseLayer.main

 albedoColor *= albedoTexel;

 float m = metalness;

#ifdef METALNESSMAP_ENABLED
 float m2 = texture2D(metalnessMap, v_DetailTexcoord)[METALNESS_CHANEL];
 m = clamp(m2 + (m - 0.5) * 2.0, 0.0, 1.0);
#endif

 vec3 baseColor = albedoColor.rgb;
 albedoColor.rgb = baseColor * (1.0 - m);
 vec3 specFactor = mix(vec3(0.04), baseColor, m);

 float g = 1.0 - roughness;

#ifdef ROUGHNESSMAP_ENABLED
 float g2 = 1.0 - texture2D(roughnessMap, v_DetailTexcoord)[ROUGHNESS_CHANEL];
 g = clamp(g2 + (g - 0.5) * 2.0, 0.0, 1.0);
#endif

 vec3 N = v_Normal;

#ifdef DOUBLE_SIDED
 if (dot(N, V) < 0.0) {
 N = -N;
 }
#endif

 float ambientFactor = 1.0;

#ifdef BUMPMAP_ENABLED
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 ambientFactor = dot(v_Normal, N);
#endif

@import ecgl.common.normalMap.fragmentMain

 vec3 N2 = vec3(N.x, N[NORMAL_UP_AXIS], N[NORMAL_FRONT_AXIS]);

 vec3 diffuseTerm = vec3(0.0);
 vec3 specularTerm = vec3(0.0);

 float ndv = clamp(dot(N, V), 0.0, 1.0);
 vec3 fresnelTerm = F_Schlick(ndv, specFactor);

 @import ecgl.common.ssaoMap.main

#ifdef AMBIENT_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_LIGHT_COUNT; _idx_++)
 {{
 diffuseTerm += ambientLightColor[_idx_] * ambientFactor * ao;
 }}
#endif

#ifdef AMBIENT_SH_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_SH_LIGHT_COUNT; _idx_++)
 {{
 diffuseTerm += calcAmbientSHLight(_idx_, N2) * ambientSHLightColor[_idx_] * ao;
 }}
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 float shadowContribsDir[DIRECTIONAL_LIGHT_COUNT];
 if(shadowEnabled)
 {
 computeShadowOfDirectionalLights(v_WorldPosition, shadowContribsDir);
 }
#endif
 for(int _idx_ = 0; _idx_ < DIRECTIONAL_LIGHT_COUNT; _idx_++)
 {{
 vec3 L = -directionalLightDirection[_idx_];
 vec3 lc = directionalLightColor[_idx_];

 vec3 H = normalize(L + V);
 float ndl = clamp(dot(N, normalize(L)), 0.0, 1.0);
 float ndh = clamp(dot(N, H), 0.0, 1.0);

 float shadowContrib = 1.0;
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 if (shadowEnabled)
 {
 shadowContrib = shadowContribsDir[_idx_];
 }
#endif

 vec3 li = lc * ndl * shadowContrib;

 diffuseTerm += li;
 specularTerm += li * fresnelTerm * D_Phong(g, ndh);
 }}
#endif


#ifdef AMBIENT_CUBEMAP_LIGHT_COUNT
 vec3 L = reflect(-V, N);
 L = vec3(L.x, L[NORMAL_UP_AXIS], L[NORMAL_FRONT_AXIS]);
 float rough2 = clamp(1.0 - g, 0.0, 1.0);
 float bias2 = rough2 * 5.0;
 vec2 brdfParam2 = texture2D(ambientCubemapLightBRDFLookup[0], vec2(rough2, ndv)).xy;
 vec3 envWeight2 = specFactor * brdfParam2.x + brdfParam2.y;
 vec3 envTexel2;
 for(int _idx_ = 0; _idx_ < AMBIENT_CUBEMAP_LIGHT_COUNT; _idx_++)
 {{
 envTexel2 = RGBMDecode(textureCubeLodEXT(ambientCubemapLightCubemap[_idx_], L, bias2), 8.12);
 specularTerm += ambientCubemapLightColor[_idx_] * envTexel2 * envWeight2 * ao;
 }}
#endif

 gl_FragColor.rgb = albedoColor.rgb * diffuseTerm + specularTerm;
 gl_FragColor.a = albedoColor.a;

#ifdef ATMOSPHERE_ENABLED
 float atmoIntensity = pow(1.0 - dot(v_Normal, (viewTranspose * vec4(0.0, 0.0, 1.0, 0.0)).xyz), glowPower);
 gl_FragColor.rgb += glowColor * atmoIntensity;
#endif

#ifdef SRGB_ENCODE
 gl_FragColor = linearTosRGB(gl_FragColor);
#endif

 @import ecgl.common.emissiveLayer.main

 @import ecgl.common.wireframe.fragmentMain
}

@end`,Qs=`@export ecgl.hatching.vertex

@import ecgl.realistic.vertex

@end


@export ecgl.hatching.fragment

#define NORMAL_UP_AXIS 1
#define NORMAL_FRONT_AXIS 2

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform vec4 color : [0.0, 0.0, 0.0, 1.0];
uniform vec4 paperColor : [1.0, 1.0, 1.0, 1.0];

uniform mat4 viewInverse : VIEWINVERSE;

#ifdef AMBIENT_LIGHT_COUNT
@import clay.header.ambient_light
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
@import clay.header.ambient_sh_light
#endif

#ifdef DIRECTIONAL_LIGHT_COUNT
@import clay.header.directional_light
#endif

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif


@import ecgl.common.ssaoMap.header

@import ecgl.common.bumpMap.header

@import clay.util.srgb

@import ecgl.common.wireframe.fragmentHeader

@import clay.plugin.compute_shadow_map

uniform sampler2D hatch1;
uniform sampler2D hatch2;
uniform sampler2D hatch3;
uniform sampler2D hatch4;
uniform sampler2D hatch5;
uniform sampler2D hatch6;

float shade(in float tone) {
 vec4 c = vec4(1. ,1., 1., 1.);
 float step = 1. / 6.;
 vec2 uv = v_DetailTexcoord;
 if (tone <= step / 2.0) {
 c = mix(vec4(0.), texture2D(hatch6, uv), 12. * tone);
 }
 else if (tone <= step) {
 c = mix(texture2D(hatch6, uv), texture2D(hatch5, uv), 6. * tone);
 }
 if(tone > step && tone <= 2. * step){
 c = mix(texture2D(hatch5, uv), texture2D(hatch4, uv) , 6. * (tone - step));
 }
 if(tone > 2. * step && tone <= 3. * step){
 c = mix(texture2D(hatch4, uv), texture2D(hatch3, uv), 6. * (tone - 2. * step));
 }
 if(tone > 3. * step && tone <= 4. * step){
 c = mix(texture2D(hatch3, uv), texture2D(hatch2, uv), 6. * (tone - 3. * step));
 }
 if(tone > 4. * step && tone <= 5. * step){
 c = mix(texture2D(hatch2, uv), texture2D(hatch1, uv), 6. * (tone - 4. * step));
 }
 if(tone > 5. * step){
 c = mix(texture2D(hatch1, uv), vec4(1.), 6. * (tone - 5. * step));
 }

 return c.r;
}

const vec3 w = vec3(0.2125, 0.7154, 0.0721);

void main()
{
#ifdef SRGB_DECODE
 vec4 inkColor = sRGBToLinear(color);
#else
 vec4 inkColor = color;
#endif

#ifdef VERTEX_COLOR
 #ifdef SRGB_DECODE
 inkColor *= sRGBToLinear(v_Color);
 #else
 inkColor *= v_Color;
 #endif
#endif

 vec3 N = v_Normal;
#ifdef DOUBLE_SIDED
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);

 if (dot(N, V) < 0.0) {
 N = -N;
 }
#endif

 float tone = 0.0;

 float ambientFactor = 1.0;

#ifdef BUMPMAP_ENABLED
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 ambientFactor = dot(v_Normal, N);
#endif

 vec3 N2 = vec3(N.x, N[NORMAL_UP_AXIS], N[NORMAL_FRONT_AXIS]);

 @import ecgl.common.ssaoMap.main

#ifdef AMBIENT_LIGHT_COUNT
 for(int i = 0; i < AMBIENT_LIGHT_COUNT; i++)
 {
 tone += dot(ambientLightColor[i], w) * ambientFactor * ao;
 }
#endif
#ifdef AMBIENT_SH_LIGHT_COUNT
 for(int _idx_ = 0; _idx_ < AMBIENT_SH_LIGHT_COUNT; _idx_++)
 {{
 tone += dot(calcAmbientSHLight(_idx_, N2) * ambientSHLightColor[_idx_], w) * ao;
 }}
#endif
#ifdef DIRECTIONAL_LIGHT_COUNT
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 float shadowContribsDir[DIRECTIONAL_LIGHT_COUNT];
 if(shadowEnabled)
 {
 computeShadowOfDirectionalLights(v_WorldPosition, shadowContribsDir);
 }
#endif
 for(int i = 0; i < DIRECTIONAL_LIGHT_COUNT; i++)
 {
 vec3 lightDirection = -directionalLightDirection[i];
 float lightTone = dot(directionalLightColor[i], w);

 float shadowContrib = 1.0;
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
 if (shadowEnabled)
 {
 shadowContrib = shadowContribsDir[i];
 }
#endif

 float ndl = dot(N, normalize(lightDirection)) * shadowContrib;

 tone += lightTone * clamp(ndl, 0.0, 1.0);
 }
#endif

 gl_FragColor = mix(inkColor, paperColor, shade(clamp(tone, 0.0, 1.0)));
 }
@end
`,Js=`@export ecgl.sm.depth.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
uniform float percent : 1.0;
#endif

varying vec4 v_ViewPosition;
varying vec2 v_Texcoord;

void main(){

#ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
#else
 vec3 pos = position;
#endif

 v_ViewPosition = worldViewProjection * vec4(pos, 1.0);
 gl_Position = v_ViewPosition;

 v_Texcoord = texcoord;

}
@end



@export ecgl.sm.depth.fragment

@import clay.sm.depth.fragment

@end`;Object.assign(Ye.prototype,Xs);z.import(qs);z.import(ua);z.import(js);z.import(Zs);z.import(Ys);z.import(Ks);z.import(Qs);z.import(Js);function $s(e){return!e||e==="none"}function ma(e){return e instanceof HTMLCanvasElement||e instanceof HTMLImageElement||e instanceof Image}function el(e){return e.getZr&&e.setOption}var tl=vt.prototype.addToScene,rl=vt.prototype.removeFromScene;vt.prototype.addToScene=function(e){if(tl.call(this,e),this.__zr){var t=this.__zr;e.traverse(function(r){r.__zr=t,r.addAnimatorsToZr&&r.addAnimatorsToZr(t)})}};vt.prototype.removeFromScene=function(e){rl.call(this,e),e.traverse(function(t){var r=t.__zr;t.__zr=null,r&&t.removeAnimatorsFromZr&&t.removeAnimatorsFromZr(r)})};at.prototype.setTextureImage=function(e,t,r,i){if(this.shader){var n=r.getZr(),a=this,o;return a.autoUpdateTextureStatus=!1,a.disableTexture(e),$s(t)||(o=w.loadTexture(t,r,i,function(s){a.enableTexture(e),n&&n.refresh()}),a.set(e,o)),o}};var w={};w.Renderer=Ve;w.Node=Ye;w.Mesh=Re;w.Shader=z;w.Material=at;w.Texture=O;w.Texture2D=K;w.Geometry=J;w.SphereGeometry=Hs;w.PlaneGeometry=Ri;w.CubeGeometry=va;w.AmbientLight=Vs;w.DirectionalLight=Gs;w.PointLight=ks;w.SpotLight=Ws;w.PerspectiveCamera=ge;w.OrthographicCamera=ur;w.Vector2=W;w.Vector3=b;w.Vector4=Z;w.Quaternion=ee;w.Matrix2=De;w.Matrix2d=Ie;w.Matrix3=pe;w.Matrix4=F;w.Plane=or;w.Ray=wt;w.BoundingBox=Ee;w.Frustum=Hr;var Sr=null;function il(){return Sr!==null||(Sr=Ke.createBlank("rgba(255,255,255,0)").image),Sr}function Sn(e){return Math.pow(2,Math.round(Math.log(e)/Math.LN2))}function wn(e){if((e.wrapS===O.REPEAT||e.wrapT===O.REPEAT)&&e.image){var t=Sn(e.width),r=Sn(e.height);if(t!==e.width||r!==e.height){var i=document.createElement("canvas");i.width=t,i.height=r;var n=i.getContext("2d");n.drawImage(e.image,0,0,t,r),e.image=i}}}w.loadTexture=function(e,t,r,i){typeof r=="function"&&(i=r,r={}),r=r||{};for(var n=Object.keys(r).sort(),a="",o=0;o<n.length;o++)a+=n[o]+"_"+r[n[o]]+"_";var s=t.__textureCache=t.__textureCache||new Za(20);if(el(e)){var l=e.__textureid__,u=s.get(a+l);if(u)u.texture.surface.setECharts(e),i&&i(u.texture);else{var f=new Si(e);f.onupdate=function(){t.getZr().refresh()},u={texture:f.getTexture()};for(var o=0;o<n.length;o++)u.texture[n[o]]=r[n[o]];l=e.__textureid__||"__ecgl_ec__"+u.texture.__uid__,e.__textureid__=l,s.put(a+l,u),i&&i(u.texture)}return u.texture}else if(ma(e)){var l=e.__textureid__,u=s.get(a+l);if(!u){u={texture:new w.Texture2D({image:e})};for(var o=0;o<n.length;o++)u.texture[n[o]]=r[n[o]];l=e.__textureid__||"__ecgl_image__"+u.texture.__uid__,e.__textureid__=l,s.put(a+l,u),wn(u.texture),i&&i(u.texture)}return u.texture}else{var u=s.get(a+e);if(u)u.callbacks?u.callbacks.push(i):i&&i(u.texture);else if(e.match(/.hdr$|^data:application\/octet-stream/)){u={callbacks:[i]};var h=Ke.loadTexture(e,{exposure:r.exposure,fileType:"hdr"},function(){h.dirty(),u.callbacks.forEach(function(v){v&&v(h)}),u.callbacks=null});u.texture=h,s.put(a+e,u)}else{for(var h=new w.Texture2D({image:new Image}),o=0;o<n.length;o++)h[n[o]]=r[n[o]];u={texture:h,callbacks:[i]};var d=h.image;d.onload=function(){h.image=d,wn(h),h.dirty(),u.callbacks.forEach(function(p){p&&p(h)}),u.callbacks=null},d.crossOrigin="Anonymous",d.src=e,h.image=il(),s.put(a+e,u)}return u.texture}};w.createAmbientCubemap=function(e,t,r,i){e=e||{};var n=e.texture,a=Ce.firstNotNull(e.exposure,1),o=new Is({intensity:Ce.firstNotNull(e.specularIntensity,1)}),s=new Bs({intensity:Ce.firstNotNull(e.diffuseIntensity,1),coefficients:[.844,.712,.691,-.037,.083,.167,.343,.288,.299,-.041,-.021,-.009,-.003,-.041,-.064,-.011,-.007,-.004,-.031,.034,.081,-.06,-.049,-.06,.046,.056,.05]});return o.cubemap=w.loadTexture(n,r,{exposure:a},function(){o.cubemap.flipY=!1,o.prefilter(t,32),s.coefficients=pa.projectEnvironmentMap(t,o.cubemap,{lod:1}),i&&i()}),{specular:o,diffuse:s}};w.createBlankTexture=Ke.createBlank;w.isImage=ma;w.additiveBlend=function(e){e.blendEquation(e.FUNC_ADD),e.blendFunc(e.SRC_ALPHA,e.ONE)};w.parseColor=function(e,t){return e instanceof Array?(t||(t=[]),t[0]=e[0],t[1]=e[1],t[2]=e[2],e.length>3?t[3]=e[3]:t[3]=1,t):(t=Yn(e||"#000",t)||[0,0,0,0],t[0]/=255,t[1]/=255,t[2]/=255,t)};w.directionFromAlphaBeta=function(e,t){var r=e/180*Math.PI+Math.PI/2,i=-t/180*Math.PI+Math.PI/2,n=[],a=Math.sin(r);return n[0]=a*Math.cos(i),n[1]=-Math.cos(r),n[2]=a*Math.sin(i),n};w.getShadowResolution=function(e){var t=1024;switch(e){case"low":t=512;break;case"medium":break;case"high":t=2048;break;case"ultra":t=4096;break}return t};w.COMMON_SHADERS=["lambert","color","realistic","hatching","shadow"];w.createShader=function(e){e==="ecgl.shadow"&&(e="ecgl.displayShadow");var t=z.source(e+".vertex"),r=z.source(e+".fragment");t||console.error("Vertex shader of '%s' not exits",e),r||console.error("Fragment shader of '%s' not exits",e);var i=new z(t,r);return i.name=e,i};w.createMaterial=function(e,t){t instanceof Array||(t=[t]);var r=w.createShader(e),i=new at({shader:r});return t.forEach(function(n){typeof n=="string"&&i.define(n)}),i};w.setMaterialFromModel=function(e,t,r,i){t.autoUpdateTextureStatus=!1;var n=r.getModel(e+"Material"),a=n.get("detailTexture"),o=Ce.firstNotNull(n.get("textureTiling"),1),s=Ce.firstNotNull(n.get("textureOffset"),0);typeof o=="number"&&(o=[o,o]),typeof s=="number"&&(s=[s,s]);var l=o[0]>1||o[1]>1?w.Texture.REPEAT:w.Texture.CLAMP_TO_EDGE,u={anisotropic:8,wrapS:l,wrapT:l};if(e==="realistic"){var f=n.get("roughness"),h=n.get("metalness");h!=null?isNaN(h)&&(t.setTextureImage("metalnessMap",h,i,u),h=Ce.firstNotNull(n.get("metalnessAdjust"),.5)):h=0,f!=null?isNaN(f)&&(t.setTextureImage("roughnessMap",f,i,u),f=Ce.firstNotNull(n.get("roughnessAdjust"),.5)):f=.5;var d=n.get("normalTexture");t.setTextureImage("detailMap",a,i,u),t.setTextureImage("normalMap",d,i,u),t.set({roughness:f,metalness:h,detailUvRepeat:o,detailUvOffset:s})}else if(e==="lambert")t.setTextureImage("detailMap",a,i,u),t.set({detailUvRepeat:o,detailUvOffset:s});else if(e==="color")t.setTextureImage("detailMap",a,i,u),t.set({detailUvRepeat:o,detailUvOffset:s});else if(e==="hatching"){var c=n.get("hatchingTextures")||[];c.length<6;for(var v=0;v<6;v++)t.setTextureImage("hatch"+(v+1),c[v],i,{anisotropic:8,wrapS:w.Texture.REPEAT,wrapT:w.Texture.REPEAT});t.set({detailUvRepeat:o,detailUvOffset:s})}};w.updateVertexAnimation=function(e,t,r,i){var n=i.get("animation"),a=i.get("animationDurationUpdate"),o=i.get("animationEasingUpdate"),s=r.shadowDepthMaterial;if(n&&t&&a>0&&t.geometry.vertexCount===r.geometry.vertexCount){r.material.define("vertex","VERTEX_ANIMATION"),r.ignorePreZ=!0,s&&s.define("vertex","VERTEX_ANIMATION");for(var l=0;l<e.length;l++)r.geometry.attributes[e[l][0]].value=t.geometry.attributes[e[l][1]].value;r.geometry.dirty(),r.__percent=0,r.material.set("percent",0),r.stopAnimation(),r.animate().when(a,{__percent:1}).during(function(){r.material.set("percent",r.__percent),s&&s.set("percent",r.__percent)}).done(function(){r.ignorePreZ=!1,r.material.undefine("vertex","VERTEX_ANIMATION"),s&&s.undefine("vertex","VERTEX_ANIMATION")}).start(o)}else r.material.undefine("vertex","VERTEX_ANIMATION"),s&&s.undefine("vertex","VERTEX_ANIMATION")};var re=function(e,t){this.id=e,this.zr=t;try{this.renderer=new Ve({clearBit:0,devicePixelRatio:t.painter.dpr,preserveDrawingBuffer:!0,premultipliedAlpha:!0}),this.renderer.resize(t.painter.getWidth(),t.painter.getHeight())}catch(i){this.renderer=null,this.dom=document.createElement("div"),this.dom.style.cssText="position:absolute; left: 0; top: 0; right: 0; bottom: 0;",this.dom.className="ecgl-nowebgl",this.dom.innerHTML="Sorry, your browser does not support WebGL",console.error(i);return}this.onglobalout=this.onglobalout.bind(this),t.on("globalout",this.onglobalout),this.dom=this.renderer.canvas;var r=this.dom.style;r.position="absolute",r.left="0",r.top="0",this.views=[],this._picking=new Pi({renderer:this.renderer}),this._viewsToDispose=[],this._accumulatingId=0,this._zrEventProxy=new Kn({shape:{x:-1,y:-1,width:2,height:2},__isGLToZRProxy:!0}),this._backgroundColor=null,this._disposed=!1};re.prototype.setUnpainted=function(){};re.prototype.addView=function(e){if(e.layer!==this){var t=this._viewsToDispose.indexOf(e);t>=0&&this._viewsToDispose.splice(t,1),this.views.push(e),e.layer=this;var r=this.zr;e.scene.traverse(function(i){i.__zr=r,i.addAnimatorsToZr&&i.addAnimatorsToZr(r)})}};function _a(e){var t=e.__zr;e.__zr=null,t&&e.removeAnimatorsFromZr&&e.removeAnimatorsFromZr(t)}re.prototype.removeView=function(e){if(e.layer===this){var t=this.views.indexOf(e);t>=0&&(this.views.splice(t,1),e.scene.traverse(_a,this),e.layer=null,this._viewsToDispose.push(e))}};re.prototype.removeViewsAll=function(){this.views.forEach(function(e){e.scene.traverse(_a,this),e.layer=null,this._viewsToDispose.push(e)},this),this.views.length=0};re.prototype.resize=function(e,t){var r=this.renderer;r.resize(e,t)};re.prototype.clear=function(){var e=this.renderer.gl,t=this._backgroundColor||[0,0,0,0];e.clearColor(t[0],t[1],t[2],t[3]),e.depthMask(!0),e.colorMask(!0,!0,!0,!0),e.clear(e.DEPTH_BUFFER_BIT|e.COLOR_BUFFER_BIT)};re.prototype.clearDepth=function(){var e=this.renderer.gl;e.clear(e.DEPTH_BUFFER_BIT)};re.prototype.clearColor=function(){var e=this.renderer.gl;e.clearColor(0,0,0,0),e.clear(e.COLOR_BUFFER_BIT)};re.prototype.needsRefresh=function(){this.zr.refresh()};re.prototype.refresh=function(e){this._backgroundColor=e?w.parseColor(e):[0,0,0,0],this.renderer.clearColor=this._backgroundColor;for(var t=0;t<this.views.length;t++)this.views[t].prepareRender(this.renderer);this._doRender(!1),this._trackAndClean();for(var t=0;t<this._viewsToDispose.length;t++)this._viewsToDispose[t].dispose(this.renderer);this._viewsToDispose.length=0,this._startAccumulating()};re.prototype.renderToCanvas=function(e){this._startAccumulating(!0),e.drawImage(this.dom,0,0,e.canvas.width,e.canvas.height)};re.prototype._doRender=function(e){this.clear(),this.renderer.saveViewport();for(var t=0;t<this.views.length;t++)this.views[t].render(this.renderer,e);this.renderer.restoreViewport()};re.prototype._stopAccumulating=function(){this._accumulatingId=0,clearTimeout(this._accumulatingTimeout)};var nl=1;re.prototype._startAccumulating=function(e){var t=this;this._stopAccumulating();for(var r=!1,i=0;i<this.views.length;i++)r=this.views[i].needsAccumulate()||r;if(!r)return;function n(a){if(!(!t._accumulatingId||a!==t._accumulatingId)){for(var o=!0,s=0;s<t.views.length;s++)o=t.views[s].isAccumulateFinished()&&r;o||(t._doRender(!0),e?n(a):Ka(function(){n(a)}))}}this._accumulatingId=nl++,e?n(t._accumulatingId):this._accumulatingTimeout=setTimeout(function(){n(t._accumulatingId)},50)};re.prototype._trackAndClean=function(){var e=[],t=[];this._textureList&&(Pr(this._textureList),Pr(this._geometriesList));for(var r=0;r<this.views.length;r++)al(this.views[r].scene,e,t);this._textureList&&(Nr(this.renderer,this._textureList),Nr(this.renderer,this._geometriesList)),this._textureList=e,this._geometriesList=t};function Pr(e){for(var t=0;t<e.length;t++)e[t].__used__=0}function Nr(e,t){for(var r=0;r<t.length;r++)t[r].__used__||t[r].dispose(e)}function wr(e,t){e.__used__=e.__used__||0,e.__used__++,e.__used__===1&&t.push(e)}function al(e,t,r){var i,n;e.traverse(function(o){if(o.isRenderable()){var s=o.geometry,l=o.material;if(l!==i)for(var u=l.getTextureUniforms(),f=0;f<u.length;f++){var h=u[f],d=l.uniforms[h].value;if(d){if(d instanceof O)wr(d,t);else if(d instanceof Array)for(var c=0;c<d.length;c++)d[c]instanceof O&&wr(d[c],t)}}s!==n&&wr(s,r),i=l,n=s}});for(var a=0;a<e.lights.length;a++)e.lights[a].cubemap&&wr(e.lights[a].cubemap,t)}re.prototype.dispose=function(){this._disposed||(this._stopAccumulating(),this._textureList&&(Pr(this._textureList),Pr(this._geometriesList),Nr(this.renderer,this._textureList),Nr(this.renderer,this._geometriesList)),this.zr.off("globalout",this.onglobalout),this._disposed=!0)};re.prototype.onmousedown=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){e=e.event;var t=this.pickObject(e.offsetX,e.offsetY);t&&(this._dispatchEvent("mousedown",e,t),this._dispatchDataEvent("mousedown",e,t)),this._downX=e.offsetX,this._downY=e.offsetY}};re.prototype.onmousemove=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){e=e.event;var t=this.pickObject(e.offsetX,e.offsetY),r=t&&t.target,i=this._hovered;this._hovered=t,i&&r!==i.target&&(i.relatedTarget=r,this._dispatchEvent("mouseout",e,i),this.zr.setCursorStyle("default")),this._dispatchEvent("mousemove",e,t),t&&(this.zr.setCursorStyle("pointer"),(!i||r!==i.target)&&this._dispatchEvent("mouseover",e,t)),this._dispatchDataEvent("mousemove",e,t)}};re.prototype.onmouseup=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){e=e.event;var t=this.pickObject(e.offsetX,e.offsetY);t&&(this._dispatchEvent("mouseup",e,t),this._dispatchDataEvent("mouseup",e,t)),this._upX=e.offsetX,this._upY=e.offsetY}};re.prototype.onclick=re.prototype.dblclick=function(e){if(!(e.target&&e.target.__isGLToZRProxy)){var t=this._upX-this._downX,r=this._upY-this._downY;if(!(Math.sqrt(t*t+r*r)>20)){e=e.event;var i=this.pickObject(e.offsetX,e.offsetY);i&&(this._dispatchEvent(e.type,e,i),this._dispatchDataEvent(e.type,e,i));var n=this._clickToSetFocusPoint(e);if(n){var a=n.view.setDOFFocusOnPoint(n.distance);a&&this.zr.refresh()}}}};re.prototype._clickToSetFocusPoint=function(e){for(var t=this.renderer,r=t.viewport,i=this.views.length-1;i>=0;i--){var n=this.views[i];if(n.hasDOF()&&n.containPoint(e.offsetX,e.offsetY)){this._picking.scene=n.scene,this._picking.camera=n.camera,t.viewport=n.viewport;var a=this._picking.pick(e.offsetX,e.offsetY,!0);if(a)return a.view=n,a}}t.viewport=r};re.prototype.onglobalout=function(e){var t=this._hovered;t&&this._dispatchEvent("mouseout",e,{target:t.target})};re.prototype.pickObject=function(e,t){for(var r=[],i=this.renderer,n=i.viewport,a=0;a<this.views.length;a++){var o=this.views[a];o.containPoint(e,t)&&(this._picking.scene=o.scene,this._picking.camera=o.camera,i.viewport=o.viewport,this._picking.pickAll(e,t,r))}return i.viewport=n,r.sort(function(s,l){return s.distance-l.distance}),r[0]};re.prototype._dispatchEvent=function(e,t,r){r||(r={});var i=r.target;for(r.cancelBubble=!1,r.event=t,r.type=e,r.offsetX=t.offsetX,r.offsetY=t.offsetY;i&&(i.trigger(e,r),i=i.getParent(),!r.cancelBubble););this._dispatchToView(e,r)};re.prototype._dispatchDataEvent=function(e,t,r){var i=r&&r.target,n=i&&i.dataIndex,a=i&&i.seriesIndex,o=i&&i.eventData,s=!1,l=this._zrEventProxy;l.x=t.offsetX,l.y=t.offsetY,l.update();var u={target:l};const f=Ya(l);e==="mousemove"&&(n!=null?n!==this._lastDataIndex&&(parseInt(this._lastDataIndex,10)>=0&&(f.dataIndex=this._lastDataIndex,f.seriesIndex=this._lastSeriesIndex,this.zr.handler.dispatchToElement(u,"mouseout",t)),s=!0):o!=null&&o!==this._lastEventData&&(this._lastEventData!=null&&(f.eventData=this._lastEventData,this.zr.handler.dispatchToElement(u,"mouseout",t)),s=!0),this._lastEventData=o,this._lastDataIndex=n,this._lastSeriesIndex=a),f.eventData=o,f.dataIndex=n,f.seriesIndex=a,(o!=null||parseInt(n,10)>=0&&parseInt(a,10)>=0)&&(this.zr.handler.dispatchToElement(u,e,t),s&&this.zr.handler.dispatchToElement(u,"mouseover",t))};re.prototype._dispatchToView=function(e,t){for(var r=0;r<this.views.length;r++)this.views[r].containPoint(t.offsetX,t.offsetY)&&this.views[r].trigger(e,t)};Object.assign(re.prototype,Di);var ol=["bar3D","line3D","map3D","scatter3D","surface","lines3D","scatterGL","scatter3D"];function ar(e,t){if(e&&e[t]&&(e[t].normal||e[t].emphasis)){var r=e[t].normal,i=e[t].emphasis;r&&(e[t]=r),i&&(e.emphasis=e.emphasis||{},e.emphasis[t]=i)}}function sl(e){ar(e,"itemStyle"),ar(e,"lineStyle"),ar(e,"areaStyle"),ar(e,"label")}function br(e){e&&(e instanceof Array||(e=[e]),bt(e,function(t){if(t.axisLabel){var r=t.axisLabel;Object.assign(r,r.textStyle),r.textStyle=null}}))}function ll(e){bt(e.series,function(t){Qa(ol,t.type)>=0&&(sl(t),t.coordinateSystem==="mapbox"&&(t.coordinateSystem="mapbox3D",e.mapbox3D=e.mapbox))}),br(e.xAxis3D),br(e.yAxis3D),br(e.zAxis3D),br(e.grid3D),ar(e.geo3D)}function ga(e){this._layers={},this._zr=e}ga.prototype.update=function(e,t){var r=this,i=t.getZr();if(!i.getWidth()||!i.getHeight()){console.warn("Dom has no width or height");return}function n(s){i.setSleepAfterStill(0);var l;s.coordinateSystem&&s.coordinateSystem.model,l=s.get("zlevel");var u=r._layers,f=u[l];if(!f){if(f=u[l]=new re("gl-"+l,i),i.painter.isSingleCanvas()){f.virtual=!0;var h=new to({z:1e4,style:{image:f.renderer.canvas},silent:!0});f.__hostImage=h,i.add(h)}i.painter.insertLayer(l,f)}return f.__hostImage&&f.__hostImage.setStyle({width:f.renderer.getWidth(),height:f.renderer.getHeight()}),f}function a(s,l){s&&s.traverse(function(u){u.isRenderable&&u.isRenderable()&&(u.ignorePicking=u.$ignorePicking!=null?u.$ignorePicking:l)})}for(var o in this._layers)this._layers[o].removeViewsAll();e.eachComponent(function(s,l){if(s!=="series"){var u=t.getViewOfComponentModel(l),f=l.coordinateSystem;if(u.__ecgl__){var h;if(f){if(!f.viewGL){console.error("Can't find viewGL in coordinateSystem of component "+l.id);return}h=f.viewGL}else{if(!l.viewGL){console.error("Can't find viewGL of component "+l.id);return}h=f.viewGL}var h=f.viewGL,d=n(l);d.addView(h),u.afterRender&&u.afterRender(l,e,t,d),a(u.groupGL,l.get("silent"))}}}),e.eachSeries(function(s){var l=t.getViewOfSeriesModel(s),u=s.coordinateSystem;if(l.__ecgl__){if(u&&!u.viewGL&&!l.viewGL){console.error("Can't find viewGL of series "+l.id);return}var f=u&&u.viewGL||l.viewGL,h=n(s);h.addView(f),l.afterRender&&l.afterRender(s,e,t,h),a(l.groupGL,s.get("silent"))}})};Ja(function(e){var t=e.getZr(),r=t.painter.dispose;t.painter.dispose=function(){typeof this.eachOtherLayer=="function"&&this.eachOtherLayer(function(i){i instanceof re&&i.dispose()}),r.call(this)},t.painter.getRenderedCanvas=function(i){if(i=i||{},this._singleCanvas)return this._layers[0].dom;var n=document.createElement("canvas"),a=i.pixelRatio||this.dpr;n.width=this.getWidth()*a,n.height=this.getHeight()*a;var o=n.getContext("2d");o.dpr=a,o.clearRect(0,0,n.width,n.height),i.backgroundColor&&(o.fillStyle=i.backgroundColor,o.fillRect(0,0,n.width,n.height));var s=this.storage.getDisplayList(!0),l={},u,f=this;function h(p,m){var _=f._zlevelList;p==null&&(p=-1/0);for(var x,T=0;T<_.length;T++){var g=_[T],E=f._layers[g];if(!E.__builtin__&&g>p&&g<m){x=E;break}}x&&x.renderToCanvas&&(o.save(),x.renderToCanvas(o),o.restore())}for(var d={ctx:o},c=0;c<s.length;c++){var v=s[c];v.zlevel!==u&&(h(u,v.zlevel),u=v.zlevel),this._doPaintEl(v,d,!0,null,l)}return h(u,1/0),n}});$a(function(e,t){var r=t.getZr(),i=r.__egl=r.__egl||new ga(r);i.update(e,t)});eo(ll);const Fe={vec2:P,vec3:y,vec4:M,mat3:k};var ul=Fe.vec3,fl=Ci.isDimensionStacked;function hl(e){var t=e[0],r=e[1];return!(t>0&&r>0||t<0&&r<0)}function cl(e,t){var r=e.getData(),i=e.get("barSize");if(i==null){var n=t.size,a,o,s=t.getAxis("x"),l=t.getAxis("y");s.type==="category"?a=s.getBandWidth()*.7:a=Math.round(n[0]/Math.sqrt(r.count()))*.6,l.type==="category"?o=l.getBandWidth()*.7:o=Math.round(n[1]/Math.sqrt(r.count()))*.6,i=[a,o]}else $e(i)||(i=[i,i]);var u=t.getAxis("z").scale.getExtent(),f=hl(u),h=["x","y","z"].map(function(v){return e.coordDimToDataDim(v)[0]}),d=fl(r,h[2]),c=d?r.getCalculationInfo("stackResultDimension"):h[2];r.each(h,function(v,p,m,_){var x=r.get(c,_),T=d?x-m:f?0:u[0],g=t.dataToPoint([v,p,T]),E=t.dataToPoint([v,p,x]),S=ul.dist(g,E),C=[0,E[1]<g[1]?-1:1,0];Math.abs(S)===0&&(S=.1);var A=[i[0],S,i[1]];r.setItemLayout(_,[g,C,A])}),r.setLayout("orient",[1,0,0])}function Ii(e,t,r){for(var i=e.getDataExtent(t),n=e.getDataExtent(r),a=i[1]-i[0]||i[0],o=n[1]-n[0]||n[0],s=50,l=new Uint8Array(s*s),u=0;u<e.count();u++){var f=e.get(t,u),h=e.get(r,u),d=Math.floor((f-i[0])/a*(s-1)),c=Math.floor((h-n[0])/o*(s-1)),v=c*s+d;l[v]=l[v]||1}for(var p=0,u=0;u<l.length;u++)l[u]&&p++;return p/l.length}var bn=Fe.vec3,dl=Ci.isDimensionStacked;function vl(e,t){var r=e.getData(),i=e.get("minHeight")||0,n=e.get("barSize"),a=["lng","lat","alt"].map(function(u){return e.coordDimToDataDim(u)[0]});if(n==null){var o=t.radius*Math.PI,s=Ii(r,a[0],a[1]);n=[o/Math.sqrt(r.count()/s),o/Math.sqrt(r.count()/s)]}else $e(n)||(n=[n,n]);var l=Bi(r,a);r.each(a,function(u,f,h,d){var c=r.get(l.dimension,d),v=l.isStacked?c-h:t.altitudeAxis.scale.getExtent()[0],p=Math.max(t.altitudeAxis.dataToCoord(h),i),m=t.dataToPoint([u,f,v]),_=t.dataToPoint([u,f,c]),x=bn.sub([],_,m);bn.normalize(x,x);var T=[n[0],p,n[1]];r.setItemLayout(d,[m,x,T])}),r.setLayout("orient",b.UP.array)}function pl(e,t){var r=e.getData(),i=e.get("barSize"),n=e.get("minHeight")||0,a=["lng","lat","alt"].map(function(f){return e.coordDimToDataDim(f)[0]});if(i==null){var o=Math.min(t.size[0],t.size[2]),s=Ii(r,a[0],a[1]);i=[o/Math.sqrt(r.count()/s),o/Math.sqrt(r.count()/s)]}else $e(i)||(i=[i,i]);var l=[0,1,0],u=Bi(r,a);r.each(a,function(f,h,d,c){var v=r.get(u.dimension,c),p=u.isStacked?v-d:t.altitudeAxis.scale.getExtent()[0],m=Math.max(t.altitudeAxis.dataToCoord(d),n),_=t.dataToPoint([f,h,p]),x=[i[0],m,i[1]];r.setItemLayout(c,[_,l,x])}),r.setLayout("orient",[1,0,0])}function ml(e,t){var r=e.getData(),i=e.coordDimToDataDim("lng")[0],n=e.coordDimToDataDim("lat")[0],a=e.coordDimToDataDim("alt")[0],o=e.get("barSize"),s=e.get("minHeight")||0;if(o==null){var l=r.getDataExtent(i),u=r.getDataExtent(n),f=t.dataToPoint([l[0],u[0]]),h=t.dataToPoint([l[1],u[1]]),d=Math.min(Math.abs(f[0]-h[0]),Math.abs(f[1]-h[1]))||1,c=Ii(r,i,n);o=[d/Math.sqrt(r.count()/c),d/Math.sqrt(r.count()/c)]}else $e(o)||(o=[o,o]),o[0]/=t.getScale()/16,o[1]/=t.getScale()/16;var v=[0,0,1],p=[i,n,a],m=Bi(r,p);r.each(p,function(_,x,T,g){var E=r.get(m.dimension,g),S=m.isStacked?E-T:0,C=t.dataToPoint([_,x,S]),A=t.dataToPoint([_,x,E]),N=Math.max(A[2]-C[2],s),H=[o[0],N,o[1]];r.setItemLayout(g,[C,v,H])}),r.setLayout("orient",[1,0,0])}function Bi(e,t){var r=dl(e,t[2]);return{dimension:r?e.getCalculationInfo("stackResultDimension"):t[2],isStacked:r}}function _l(e){e.registerLayout(function(t,r){t.eachSeriesByType("bar3D",function(i){var n=i.coordinateSystem,a=n&&n.type;a==="globe"?vl(i,n):a==="cartesian3D"?cl(i,n):a==="geo3D"?pl(i,n):(a==="mapbox3D"||a==="maptalks3D")&&ml(i,n)})})}const gl={defaultOption:{shading:null,realisticMaterial:{textureTiling:1,textureOffset:0,detailTexture:null},lambertMaterial:{textureTiling:1,textureOffset:0,detailTexture:null},colorMaterial:{textureTiling:1,textureOffset:0,detailTexture:null},hatchingMaterial:{textureTiling:1,textureOffset:0,paperColor:"#fff"}}};var qt={};qt.getFormattedLabel=function(e,t,r,i,n){r=r||"normal";var a=e.getData(i),o=a.getItemModel(t),s=e.getDataParams(t,i);n!=null&&s.value instanceof Array&&(s.value=s.value[n]);var l=o.get(r==="normal"?["label","formatter"]:["emphasis","label","formatter"]);l==null&&(l=o.get(["label","formatter"]));var u;return typeof l=="function"?(s.status=r,u=l(s)):typeof l=="string"&&(u=ro(l,s)),u};qt.normalizeToArray=function(e){return e instanceof Array?e:e==null?[]:[e]};function yl(e){const t=e.getVisual("style");if(t){const r=e.getVisual("drawType");return t[r]}}function xl(e){return e.getVisual("style").opacity}function Je(e,t){const r=e.getItemVisual(t,"style");if(r){const i=e.getVisual("drawType");return r[i]}}function nt(e,t){const r=e.getItemVisual(t,"style");return r&&r.opacity}function Tl(e,t){var r=[];return bt(e.dimensions,function(i){var n=e.getDimensionInfo(i),a=n.otherDims,o=a[t];o!=null&&o!==!1&&(r[o]=n.name)}),r}function ya(e,t,r){function i(h){var d=[],c=Tl(n,"tooltip");c.length?bt(c,function(p){v(n.get(p,t),p)}):bt(h,v);function v(p,m){var _=n.getDimensionInfo(m);if(!(!_||_.otherDims.tooltip===!1)){var x=_.type,T="- "+(_.tooltipName||_.name)+": "+(x==="ordinal"?p+"":x==="time"?ao("yyyy/MM/dd hh:mm:ss",p):Wi(p));T&&d.push(vr(T))}}return"<br/>"+d.join("<br/>")}var n=e.getData(),a=e.getRawValue(t),o=$e(a)?i(a):vr(Wi(a)),s=n.getName(t),l=Je(n,t);io(l)&&l.colorStops&&(l=(l.colorStops[0]||{}).color),l=l||"transparent";var u=no(l),f=e.name;return f==="\0-"&&(f=""),f=f?vr(f)+"<br/>":"",f+u+(s?vr(s)+": "+o:o)}function xa(e,t,r){r=r||e.getSource();var i=oo(e.get("coordinateSystem"))||["x","y","z"],n=so(r,{dimensionsDefine:r.dimensionsDefine||e.get("dimensions"),encodeDefine:r.encodeDefine||e.get("encode"),coordDimensions:i.map(function(s){var l=e.getReferringComponents(s+"Axis3D").models[0];return{type:l&&l.get("type")==="category"?"ordinal":"float",name:s}})});e.get("coordinateSystem")==="cartesian3D"&&n.forEach(function(s){if(i.indexOf(s.coordDim)>=0){var l=e.getReferringComponents(s.coordDim+"Axis3D").models[0];l&&l.get("type")==="category"&&(s.ordinalMeta=l.getOrdinalMeta())}});var a=Ci.enableDataStack(e,n,{byIndex:!0,stackedCoordDimension:"z"}),o=new Qn(n,e);return o.setCalculationInfo(a),o.initData(r),o}var Ta=Li.extend({type:"series.bar3D",dependencies:["globe"],visualStyleAccessPathvisu:"itemStyle",getInitialData:function(e,t){return xa(this)},getFormattedLabel:function(e,t,r,i){var n=qt.getFormattedLabel(this,e,t,r,i);return n==null&&(n=this.getData().get("z",e)),n},formatTooltip:function(e){return ya(this,e)},defaultOption:{coordinateSystem:"cartesian3D",globeIndex:0,grid3DIndex:0,zlevel:-10,bevelSize:0,bevelSmoothness:2,onGridPlane:"xy",shading:"color",minHeight:0,itemStyle:{opacity:1},label:{show:!1,distance:2,textStyle:{fontSize:14,color:"#000",backgroundColor:"rgba(255,255,255,0.7)",padding:3,borderRadius:3}},emphasis:{label:{show:!0}},animationDurationUpdate:500}});it(Ta.prototype,gl);const Gr={convertToDynamicArray:function(e){e&&this.resetOffset();var t=this.attributes;for(var r in t)e||!t[r].value?t[r].value=[]:t[r].value=Array.prototype.slice.call(t[r].value);e||!this.indices?this.indices=[]:this.indices=Array.prototype.slice.call(this.indices)},convertToTypedArray:function(){var e=this.attributes;for(var t in e)e[t].value&&e[t].value.length>0?e[t].value=new Float32Array(e[t].value):e[t].value=null;this.indices&&this.indices.length>0&&(this.indices=this.vertexCount>65535?new Uint32Array(this.indices):new Uint16Array(this.indices)),this.dirty()}};function ui(e,t,r){var i=e[t];e[t]=e[r],e[r]=i}function Ea(e,t,r,i,n){var a=r,o=e[t];ui(e,t,i);for(var s=r;s<i;s++)n(e[s],o)<0&&(ui(e,s,a),a++);return ui(e,i,a),a}function Rr(e,t,r,i){if(r<i){var n=Math.floor((r+i)/2),a=Ea(e,n,r,i,t);Rr(e,t,r,a-1),Rr(e,t,a+1,i)}}function Wt(){this._parts=[]}Wt.prototype.step=function(e,t,r){var i=e.length;if(r===0){this._parts=[],this._sorted=!1;var n=Math.floor(i/2);this._parts.push({pivot:n,left:0,right:i-1}),this._currentSortPartIdx=0}if(!this._sorted){var a=this._parts;if(a.length===0)return this._sorted=!0,!0;if(a.length<512){for(var o=0;o<a.length;o++)a[o].pivot=Ea(e,a[o].pivot,a[o].left,a[o].right,t);for(var s=[],o=0;o<a.length;o++){var l=a[o].left,u=a[o].pivot-1;u>l&&s.push({pivot:Math.floor((u+l)/2),left:l,right:u});var l=a[o].pivot+1,u=a[o].right;u>l&&s.push({pivot:Math.floor((u+l)/2),left:l,right:u})}a=this._parts=s}else for(var o=0;o<Math.floor(a.length/10);o++){var f=a.length-1-this._currentSortPartIdx;if(Rr(e,t,a[f].left,a[f].right),this._currentSortPartIdx++,this._currentSortPartIdx===a.length)return this._sorted=!0,!0}return!1}};Wt.sort=Rr;var zt=Fe.vec3,An=zt.create(),Cn=zt.create(),Ln=zt.create();const El={needsSortTriangles:function(){return this.indices&&this.sortTriangles},needsSortTrianglesProgressively:function(){return this.needsSortTriangles()&&this.triangleCount>=2e4},doSortTriangles:function(e,t){var r=this.indices;if(t===0){var i=this.attributes.position,e=e.array;(!this._triangleZList||this._triangleZList.length!==this.triangleCount)&&(this._triangleZList=new Float32Array(this.triangleCount),this._sortedTriangleIndices=new Uint32Array(this.triangleCount),this._indicesTmp=new r.constructor(r.length),this._triangleZListTmp=new Float32Array(this.triangleCount));for(var n=0,a,o=0;o<r.length;){i.get(r[o++],An),i.get(r[o++],Cn),i.get(r[o++],Ln);var s=zt.sqrDist(An,e),l=zt.sqrDist(Cn,e),u=zt.sqrDist(Ln,e),f=Math.min(s,l);f=Math.min(f,u),o===3?(a=f,f=0):f=f-a,this._triangleZList[n++]=f}}for(var h=this._sortedTriangleIndices,o=0;o<h.length;o++)h[o]=o;if(this.triangleCount<2e4)t===0&&this._simpleSort(!0);else for(var o=0;o<3;o++)this._progressiveQuickSort(t*3+o);for(var d=this._indicesTmp,c=this._triangleZListTmp,v=this._triangleZList,o=0;o<this.triangleCount;o++){var p=h[o]*3,m=o*3;d[m++]=r[p++],d[m++]=r[p++],d[m]=r[p],c[o]=v[h[o]]}var _=this._indicesTmp;this._indicesTmp=this.indices,this.indices=_;var _=this._triangleZListTmp;this._triangleZListTmp=this._triangleZList,this._triangleZList=_,this.dirtyIndices()},_simpleSort:function(e){var t=this._triangleZList,r=this._sortedTriangleIndices;function i(n,a){return t[a]-t[n]}e?Array.prototype.sort.call(r,i):Wt.sort(r,i,0,r.length-1)},_progressiveQuickSort:function(e){var t=this._triangleZList,r=this._sortedTriangleIndices;this._quickSort=this._quickSort||new Wt,this._quickSort.step(r,function(i,n){return t[n]-t[i]},e)}};var ue=Fe.vec3,Sl=Fe.mat3,Fi=J.extend(function(){return{attributes:{position:new J.Attribute("position","float",3,"POSITION"),normal:new J.Attribute("normal","float",3,"NORMAL"),color:new J.Attribute("color","float",4,"COLOR"),prevPosition:new J.Attribute("prevPosition","float",3),prevNormal:new J.Attribute("prevNormal","float",3)},dynamic:!0,enableNormal:!1,bevelSize:1,bevelSegments:0,_dataIndices:null,_vertexOffset:0,_triangleOffset:0}},{resetOffset:function(){this._vertexOffset=0,this._triangleOffset=0},setBarCount:function(e){var t=this.enableNormal,r=this.getBarVertexCount()*e,i=this.getBarTriangleCount()*e;this.vertexCount!==r&&(this.attributes.position.init(r),t?this.attributes.normal.init(r):this.attributes.normal.value=null,this.attributes.color.init(r)),this.triangleCount!==i&&(this.indices=r>65535?new Uint32Array(i*3):new Uint16Array(i*3),this._dataIndices=new Uint32Array(r))},getBarVertexCount:function(){var e=this.bevelSize>0?this.bevelSegments:0;return e>0?this._getBevelBarVertexCount(e):this.enableNormal?24:8},getBarTriangleCount:function(){var e=this.bevelSize>0?this.bevelSegments:0;return e>0?this._getBevelBarTriangleCount(e):12},_getBevelBarVertexCount:function(e){return(e+1)*4*(e+1)*2},_getBevelBarTriangleCount:function(e){var t=e*4+3,r=e*2+1;return(t+1)*r*2+4},setColor:function(e,t){for(var r=this.getBarVertexCount(),i=r*e,n=r*(e+1),a=i;a<n;a++)this.attributes.color.set(a,t);this.dirtyAttribute("color")},getDataIndexOfVertex:function(e){return this._dataIndices?this._dataIndices[e]:null},addBar:(function(){for(var e=ue.create,t=ue.scaleAndAdd,r=e(),i=e(),n=e(),a=e(),o=e(),s=e(),l=e(),u=[],f=[],h=0;h<8;h++)u[h]=e();for(var d=[[0,1,5,4],[2,3,7,6],[4,5,6,7],[3,2,1,0],[0,4,7,3],[1,2,6,5]],c=[0,1,2,0,2,3],v=[],h=0;h<d.length;h++)for(var p=d[h],m=0;m<2;m++){for(var _=[],x=0;x<3;x++)_.push(p[c[m*3+x]]);v.push(_)}return function(T,g,E,S,C,A){var N=this._vertexOffset;if(this.bevelSize>0&&this.bevelSegments>0)this._addBevelBar(T,g,E,S,this.bevelSize,this.bevelSegments,C);else{ue.copy(n,g),ue.normalize(n,n),ue.cross(a,E,n),ue.normalize(a,a),ue.cross(i,n,a),ue.normalize(a,a),ue.negate(o,i),ue.negate(s,n),ue.negate(l,a),t(u[0],T,i,S[0]/2),t(u[0],u[0],a,S[2]/2),t(u[1],T,i,S[0]/2),t(u[1],u[1],l,S[2]/2),t(u[2],T,o,S[0]/2),t(u[2],u[2],l,S[2]/2),t(u[3],T,o,S[0]/2),t(u[3],u[3],a,S[2]/2),t(r,T,n,S[1]),t(u[4],r,i,S[0]/2),t(u[4],u[4],a,S[2]/2),t(u[5],r,i,S[0]/2),t(u[5],u[5],l,S[2]/2),t(u[6],r,o,S[0]/2),t(u[6],u[6],l,S[2]/2),t(u[7],r,o,S[0]/2),t(u[7],u[7],a,S[2]/2);var H=this.attributes;if(this.enableNormal){f[0]=i,f[1]=o,f[2]=n,f[3]=s,f[4]=a,f[5]=l;for(var R=this._vertexOffset,U=0;U<d.length;U++){for(var V=this._triangleOffset*3,I=0;I<6;I++)this.indices[V++]=R+c[I];R+=4,this._triangleOffset+=2}for(var U=0;U<d.length;U++)for(var G=f[U],I=0;I<4;I++){var X=d[U][I];H.position.set(this._vertexOffset,u[X]),H.normal.set(this._vertexOffset,G),H.color.set(this._vertexOffset++,C)}}else{for(var U=0;U<v.length;U++){for(var V=this._triangleOffset*3,I=0;I<3;I++)this.indices[V+I]=v[U][I]+this._vertexOffset;this._triangleOffset++}for(var U=0;U<u.length;U++)H.position.set(this._vertexOffset,u[U]),H.color.set(this._vertexOffset++,C)}}for(var q=this._vertexOffset,U=N;U<q;U++)this._dataIndices[U]=A}})(),_addBevelBar:(function(){var e=ue.create(),t=ue.create(),r=ue.create(),i=Sl.create(),n=[],a=[1,-1,-1,1],o=[1,1,-1,-1],s=[2,0];return function(l,u,f,h,d,c,v){ue.copy(t,u),ue.normalize(t,t),ue.cross(r,f,t),ue.normalize(r,r),ue.cross(e,t,r),ue.normalize(r,r),i[0]=e[0],i[1]=e[1],i[2]=e[2],i[3]=t[0],i[4]=t[1],i[5]=t[2],i[6]=r[0],i[7]=r[1],i[8]=r[2],d=Math.min(h[0],h[2])/2*d;for(var p=0;p<3;p++)n[p]=Math.max(h[p]-d*2,0);for(var m=(h[0]-n[0])/2,_=(h[1]-n[1])/2,x=(h[2]-n[2])/2,T=[],g=[],E=this._vertexOffset,S=[],p=0;p<2;p++){S[p]=S[p]=[];for(var C=0;C<=c;C++)for(var A=0;A<4;A++){(C===0&&p===0||p===1&&C===c)&&S[p].push(E);for(var N=0;N<=c;N++){var H=N/c*Math.PI/2+Math.PI/2*A,R=C/c*Math.PI/2+Math.PI/2*p;g[0]=m*Math.cos(H)*Math.sin(R),g[1]=_*Math.cos(R),g[2]=x*Math.sin(H)*Math.sin(R),T[0]=g[0]+a[A]*n[0]/2,T[1]=g[1]+_+s[p]*n[1]/2,T[2]=g[2]+o[A]*n[2]/2,Math.abs(m-_)<1e-6&&Math.abs(_-x)<1e-6||(g[0]/=m*m,g[1]/=_*_,g[2]/=x*x),ue.normalize(g,g),ue.transformMat3(T,T,i),ue.transformMat3(g,g,i),ue.add(T,T,l),this.attributes.position.set(E,T),this.enableNormal&&this.attributes.normal.set(E,g),this.attributes.color.set(E,v),E++}}}for(var U=c*4+3,V=c*2+1,I=U+1,A=0;A<V;A++)for(var p=0;p<=U;p++){var G=A*I+p+this._vertexOffset,X=A*I+(p+1)%I+this._vertexOffset,q=(A+1)*I+(p+1)%I+this._vertexOffset,ie=(A+1)*I+p+this._vertexOffset;this.setTriangleIndices(this._triangleOffset++,[q,G,X]),this.setTriangleIndices(this._triangleOffset++,[q,ie,G])}this.setTriangleIndices(this._triangleOffset++,[S[0][0],S[0][2],S[0][1]]),this.setTriangleIndices(this._triangleOffset++,[S[0][0],S[0][3],S[0][2]]),this.setTriangleIndices(this._triangleOffset++,[S[1][0],S[1][1],S[1][2]]),this.setTriangleIndices(this._triangleOffset++,[S[1][0],S[1][2],S[1][3]]),this._vertexOffset=E}})()});Ct(Fi.prototype,Gr);Ct(Fi.prototype,El);function Or(e,t,r,i,n,a,o){this._zr=e,this._x=0,this._y=0,this._rowHeight=0,this.width=i,this.height=n,this.offsetX=t,this.offsetY=r,this.dpr=o,this.gap=a}Or.prototype={constructor:Or,clear:function(){this._x=0,this._y=0,this._rowHeight=0},add:function(e,t,r){var i=e.getBoundingRect();t==null&&(t=i.width),r==null&&(r=i.height),t*=this.dpr,r*=this.dpr,this._fitElement(e,t,r);var n=this._x,a=this._y,o=this.width*this.dpr,s=this.height*this.dpr,l=this.gap;if(n+t+l>o&&(n=this._x=0,a+=this._rowHeight+l,this._y=a,this._rowHeight=0),this._x+=t+l,this._rowHeight=Math.max(this._rowHeight,r),a+r+l>s)return null;e.x+=this.offsetX*this.dpr+n,e.y+=this.offsetY*this.dpr+a,this._zr.add(e);var u=[this.offsetX/this.width,this.offsetY/this.height],f=[[n/o+u[0],a/s+u[1]],[(n+t)/o+u[0],(a+r)/s+u[1]]];return f},_fitElement:function(e,t,r){var i=e.getBoundingRect(),n=t/i.width,a=r/i.height;e.x=-i.x*n,e.y=-i.y*a,e.scaleX=n,e.scaleY=a,e.update()}};function Ir(e){e=e||{},e.width=e.width||512,e.height=e.height||512,e.devicePixelRatio=e.devicePixelRatio||1,e.gap=e.gap==null?2:e.gap;var t=document.createElement("canvas");t.width=e.width*e.devicePixelRatio,t.height=e.height*e.devicePixelRatio,this._canvas=t,this._texture=new K({image:t,flipY:!1});var r=this;this._zr=lo(t);var i=this._zr.refreshImmediately;this._zr.refreshImmediately=function(){i.call(this),r._texture.dirty(),r.onupdate&&r.onupdate()},this._dpr=e.devicePixelRatio,this._coords={},this.onupdate=e.onupdate,this._gap=e.gap,this._textureAtlasNodes=[new Or(this._zr,0,0,e.width,e.height,this._gap,this._dpr)],this._nodeWidth=e.width,this._nodeHeight=e.height,this._currentNodeIdx=0}Ir.prototype={clear:function(){for(var e=0;e<this._textureAtlasNodes.length;e++)this._textureAtlasNodes[e].clear();this._currentNodeIdx=0,this._zr.clear(),this._coords={}},getWidth:function(){return this._width},getHeight:function(){return this._height},getTexture:function(){return this._texture},getDevicePixelRatio:function(){return this._dpr},getZr:function(){return this._zr},_getCurrentNode:function(){return this._textureAtlasNodes[this._currentNodeIdx]},_expand:function(){if(this._currentNodeIdx++,this._textureAtlasNodes[this._currentNodeIdx])return this._textureAtlasNodes[this._currentNodeIdx];var e=4096/this._dpr,t=this._textureAtlasNodes,r=t.length,i=r*this._nodeWidth%e,n=Math.floor(r*this._nodeWidth/e)*this._nodeHeight;if(!(n>=e)){var a=(i+this._nodeWidth)*this._dpr,o=(n+this._nodeHeight)*this._dpr;try{this._zr.resize({width:a,height:o})}catch{this._canvas.width=a,this._canvas.height=o}var s=new Or(this._zr,i,n,this._nodeWidth,this._nodeHeight,this._gap,this._dpr);return this._textureAtlasNodes.push(s),s}},add:function(e,t,r){if(this._coords[e.id])return this._coords[e.id];var i=this._getCurrentNode().add(e,t,r);if(!i){var n=this._expand();if(!n)return;i=n.add(e,t,r)}return this._coords[e.id]=i,i},getCoordsScale:function(){var e=this._dpr;return[this._nodeWidth/this._canvas.width*e,this._nodeHeight/this._canvas.height*e]},getCoords:function(e){return this._coords[e]},dispose:function(){this._zr.dispose()}};var Mn=[0,1,2,0,2,3],Sa=J.extend(function(){return{attributes:{position:new J.Attribute("position","float",3,"POSITION"),texcoord:new J.Attribute("texcoord","float",2,"TEXCOORD_0"),offset:new J.Attribute("offset","float",2),color:new J.Attribute("color","float",4,"COLOR")}}},{resetOffset:function(){this._vertexOffset=0,this._faceOffset=0},setSpriteCount:function(e){this._spriteCount=e;var t=e*4,r=e*2;this.vertexCount!==t&&(this.attributes.position.init(t),this.attributes.offset.init(t),this.attributes.color.init(t)),this.triangleCount!==r&&(this.indices=t>65535?new Uint32Array(r*3):new Uint16Array(r*3))},setSpriteAlign:function(e,t,r,i,n){r==null&&(r="left"),i==null&&(i="top");var a,o,s,l;switch(n=n||0,r){case"left":a=n,s=t[0]+n;break;case"center":case"middle":a=-t[0]/2,s=t[0]/2;break;case"right":a=-t[0]-n,s=-n;break}switch(i){case"bottom":o=n,l=t[1]+n;break;case"middle":o=-t[1]/2,l=t[1]/2;break;case"top":o=-t[1]-n,l=-n;break}var u=e*4,f=this.attributes.offset;f.set(u,[a,l]),f.set(u+1,[s,l]),f.set(u+2,[s,o]),f.set(u+3,[a,o])},addSprite:function(e,t,r,i,n,a){var o=this._vertexOffset;this.setSprite(this._vertexOffset/4,e,t,r,i,n,a);for(var s=0;s<Mn.length;s++)this.indices[this._faceOffset*3+s]=Mn[s]+o;return this._faceOffset+=2,this._vertexOffset+=4,o/4},setSprite:function(e,t,r,i,n,a,o){for(var s=e*4,l=this.attributes,u=0;u<4;u++)l.position.set(s+u,t);var f=l.texcoord;f.set(s,[i[0][0],i[0][1]]),f.set(s+1,[i[1][0],i[0][1]]),f.set(s+2,[i[1][0],i[1][1]]),f.set(s+3,[i[0][0],i[1][1]]),this.setSpriteAlign(e,r,n,a,o)}});Ct(Sa.prototype,Gr);const wl=`@export ecgl.labels.vertex

attribute vec3 position: POSITION;
attribute vec2 texcoord: TEXCOORD_0;
attribute vec2 offset;
#ifdef VERTEX_COLOR
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;
#endif

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform vec4 viewport : VIEWPORT;

varying vec2 v_Texcoord;

void main()
{
 vec4 proj = worldViewProjection * vec4(position, 1.0);

 vec2 screen = (proj.xy / abs(proj.w) + 1.0) * 0.5 * viewport.zw;

 screen += offset;

 proj.xy = (screen / viewport.zw - 0.5) * 2.0 * abs(proj.w);
 gl_Position = proj;
#ifdef VERTEX_COLOR
 v_Color = a_Color;
#endif
 v_Texcoord = texcoord;
}
@end


@export ecgl.labels.fragment

uniform vec3 color : [1.0, 1.0, 1.0];
uniform float alpha : 1.0;
uniform sampler2D textureAtlas;
uniform vec2 uvScale: [1.0, 1.0];

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif
varying float v_Miter;

varying vec2 v_Texcoord;

void main()
{
 gl_FragColor = vec4(color, alpha) * texture2D(textureAtlas, v_Texcoord * uvScale);
#ifdef VERTEX_COLOR
 gl_FragColor *= v_Color;
#endif
}

@end`;w.Shader.import(wl);const Ui=w.Mesh.extend(function(){var e=new Sa({dynamic:!0}),t=new w.Material({shader:w.createShader("ecgl.labels"),transparent:!0,depthMask:!1});return{geometry:e,material:t,culling:!1,castShadow:!1,ignorePicking:!0}});var wa=1,ba=2;function pt(e,t,r){this._labelsMesh=new Ui,this._labelTextureSurface=new Ir({width:512,height:512,devicePixelRatio:r.getDevicePixelRatio(),onupdate:function(){r.getZr().refresh()}}),this._api=r,this._labelsMesh.material.set("textureAtlas",this._labelTextureSurface.getTexture())}pt.prototype.getLabelPosition=function(e,t,r){return[0,0,0]};pt.prototype.getLabelDistance=function(e,t,r){return 0};pt.prototype.getMesh=function(){return this._labelsMesh};pt.prototype.updateData=function(e,t,r){t==null&&(t=0),r==null&&(r=e.count()),(!this._labelsVisibilitiesBits||this._labelsVisibilitiesBits.length!==r-t)&&(this._labelsVisibilitiesBits=new Uint8Array(r-t));for(var i=["label","show"],n=["emphasis","label","show"],a=t;a<r;a++){var o=e.getItemModel(a),s=o.get(i),l=o.get(n);l==null&&(l=s);var u=(s?wa:0)|(l?ba:0);this._labelsVisibilitiesBits[a-t]=u}this._start=t,this._end=r,this._data=e};pt.prototype.updateLabels=function(e){if(this._data){e=e||[];for(var t=e.length>0,r={},i=0;i<e.length;i++)r[e[i]]=!0;this._labelsMesh.geometry.convertToDynamicArray(!0),this._labelTextureSurface.clear();for(var n=["label"],a=["emphasis","label"],o=this._data.hostModel,s=this._data,l=o.getModel(n),u=o.getModel(a,l),f={left:"right",right:"left",top:"center",bottom:"center"},h={left:"middle",right:"middle",top:"bottom",bottom:"top"},d=this._start;d<this._end;d++){var c=!1;t&&r[d]&&(c=!0);var v=this._labelsVisibilitiesBits[d-this._start]&(c?ba:wa);if(v){var p=s.getItemModel(d),m=p.getModel(c?a:n,c?u:l),_=m.get("distance")||0,x=m.get("position"),T=this._api.getDevicePixelRatio(),g=o.getFormattedLabel(d,c?"emphasis":"normal");if(g==null||g==="")return;var E=new Mr({style:Dr(m,{text:g,fill:m.get("color")||Je(s,d)||"#000",align:"left",verticalAlign:"top",opacity:Ce.firstNotNull(m.get("opacity"),nt(s,d),1)})}),S=E.getBoundingRect(),C=1.2;S.height*=C;var A=this._labelTextureSurface.add(E),N=f[x]||"center",H=h[x]||"bottom";this._labelsMesh.geometry.addSprite(this.getLabelPosition(d,x,_),[S.width*T,S.height*T],A,N,H,this.getLabelDistance(d,x,_)*T)}}this._labelsMesh.material.set("uvScale",this._labelTextureSurface.getCoordsScale()),this._labelTextureSurface.getZr().refreshImmediately(),this._labelsMesh.geometry.convertToTypedArray(),this._labelsMesh.geometry.dirty()}};pt.prototype.dispose=function(){this._labelTextureSurface.dispose()};var bl=Fe.vec3;const Al=Mi.extend({type:"bar3D",__ecgl__:!0,init:function(e,t){this.groupGL=new w.Node,this._api=t,this._labelsBuilder=new pt(256,256,t);var r=this;this._labelsBuilder.getLabelPosition=function(i,n,a){if(r._data){var o=r._data.getItemLayout(i),s=o[0],l=o[1],u=o[2][1];return bl.scaleAndAdd([],s,l,a+u)}else return[0,0]},this._labelsBuilder.getMesh().renderOrder=100},render:function(e,t,r){var i=this._prevBarMesh;this._prevBarMesh=this._barMesh,this._barMesh=i,this._barMesh||(this._barMesh=new w.Mesh({geometry:new Fi,shadowDepthMaterial:new w.Material({shader:new w.Shader(w.Shader.source("ecgl.sm.depth.vertex"),w.Shader.source("ecgl.sm.depth.fragment"))}),culling:e.coordinateSystem.type==="cartesian3D",renderOrder:10,renderNormal:!0})),this.groupGL.remove(this._prevBarMesh),this.groupGL.add(this._barMesh),this.groupGL.add(this._labelsBuilder.getMesh());var n=e.coordinateSystem;if(this._doRender(e,r),n&&n.viewGL){n.viewGL.add(this.groupGL);var a=n.viewGL.isLinearSpace()?"define":"undefine";this._barMesh.material[a]("fragment","SRGB_DECODE")}this._data=e.getData(),this._labelsBuilder.updateData(this._data),this._labelsBuilder.updateLabels(),this._updateAnimation(e)},_updateAnimation:function(e){w.updateVertexAnimation([["prevPosition","position"],["prevNormal","normal"]],this._prevBarMesh,this._barMesh,e)},_doRender:function(e,t){var r=e.getData(),i=e.get("shading"),n=i!=="color",a=this,o=this._barMesh,s="ecgl."+i;(!o.material||o.material.shader.name!==s)&&(o.material=w.createMaterial(s,["VERTEX_COLOR"])),w.setMaterialFromModel(i,o.material,e,t),o.geometry.enableNormal=n,o.geometry.resetOffset();var l=e.get("bevelSize"),u=e.get("bevelSmoothness");o.geometry.bevelSegments=u,o.geometry.bevelSize=l;var f=[],h=new Float32Array(r.count()*4),d=0,m=0,c=!1;r.each(function(x){if(r.hasValue(x)){var T=Je(r,x),g=nt(r,x);g==null&&(g=1),w.parseColor(T,f),f[3]*=g,h[d++]=f[0],h[d++]=f[1],h[d++]=f[2],h[d++]=f[3],f[3]>0&&(m++,f[3]<.99&&(c=!0))}}),o.geometry.setBarCount(m);var v=r.getLayout("orient"),p=this._barIndexOfData=new Int32Array(r.count()),m=0;r.each(function(x){if(!r.hasValue(x)){p[x]=-1;return}var T=r.getItemLayout(x),g=T[0],E=T[1],S=T[2],C=x*4;f[0]=h[C++],f[1]=h[C++],f[2]=h[C++],f[3]=h[C++],f[3]>0&&(a._barMesh.geometry.addBar(g,E,v,S,f,x),p[x]=m++)}),o.geometry.dirty(),o.geometry.updateBoundingBox();var _=o.material;_.transparent=c,_.depthMask=!c,o.geometry.sortTriangles=c,this._initHandler(e,t)},_initHandler:function(e,t){var r=e.getData(),i=this._barMesh,n=e.coordinateSystem.type==="cartesian3D";i.seriesIndex=e.seriesIndex;var a=-1;i.off("mousemove"),i.off("mouseout"),i.on("mousemove",function(o){var s=i.geometry.getDataIndexOfVertex(o.triangle[0]);s!==a&&(this._downplay(a),this._highlight(s),this._labelsBuilder.updateLabels([s]),n&&t.dispatchAction({type:"grid3DShowAxisPointer",value:[r.get("x",s),r.get("y",s),r.get("z",s,!0)]})),a=s,i.dataIndex=s},this),i.on("mouseout",function(o){this._downplay(a),this._labelsBuilder.updateLabels(),a=-1,i.dataIndex=-1,n&&t.dispatchAction({type:"grid3DHideAxisPointer"})},this)},_highlight:function(e){var t=this._data;if(t){var r=this._barIndexOfData[e];if(!(r<0)){var i=t.getItemModel(e),n=i.getModel("emphasis.itemStyle"),a=n.get("color"),o=n.get("opacity");if(a==null){var s=Je(t,e);a=Jn(s,-.4)}o==null&&(o=nt(t,e));var l=w.parseColor(a);l[3]*=o,this._barMesh.geometry.setColor(r,l),this._api.getZr().refresh()}}},_downplay:function(e){var t=this._data;if(t){var r=this._barIndexOfData[e];if(!(r<0)){var i=Je(t,e),n=nt(t,e),a=w.parseColor(i);a[3]*=n,this._barMesh.geometry.setColor(r,a),this._api.getZr().refresh()}}},highlight:function(e,t,r,i){this._toggleStatus("highlight",e,t,r,i)},downplay:function(e,t,r,i){this._toggleStatus("downplay",e,t,r,i)},_toggleStatus:function(e,t,r,i,n){var a=t.getData(),o=Ce.queryDataIndex(a,n),s=this;o!=null?bt(qt.normalizeToArray(o),function(l){e==="highlight"?this._highlight(l):this._downplay(l)},this):a.each(function(l){e==="highlight"?s._highlight(l):s._downplay(l)})},remove:function(){this.groupGL.removeAll()},dispose:function(){this._labelsBuilder.dispose(),this.groupGL.removeAll()}});function Iu(e){e.registerChartView(Al),e.registerSeriesModel(Ta),_l(e),e.registerProcessor(function(t,r){t.eachSeriesByType("bar3d",function(i){var n=i.getData();n.filterSelf(function(a){return n.hasValue(a)})})})}var fi=Fe.vec3,Dn=[[0,0],[1,1]],jt=J.extend(function(){return{segmentScale:1,dynamic:!0,useNativeLine:!0,attributes:{position:new J.Attribute("position","float",3,"POSITION"),positionPrev:new J.Attribute("positionPrev","float",3),positionNext:new J.Attribute("positionNext","float",3),prevPositionPrev:new J.Attribute("prevPositionPrev","float",3),prevPosition:new J.Attribute("prevPosition","float",3),prevPositionNext:new J.Attribute("prevPositionNext","float",3),offset:new J.Attribute("offset","float",1),color:new J.Attribute("color","float",4,"COLOR")}}},{resetOffset:function(){this._vertexOffset=0,this._triangleOffset=0,this._itemVertexOffsets=[]},setVertexCount:function(e){var t=this.attributes;this.vertexCount!==e&&(t.position.init(e),t.color.init(e),this.useNativeLine||(t.positionPrev.init(e),t.positionNext.init(e),t.offset.init(e)),e>65535?this.indices instanceof Uint16Array&&(this.indices=new Uint32Array(this.indices)):this.indices instanceof Uint32Array&&(this.indices=new Uint16Array(this.indices)))},setTriangleCount:function(e){this.triangleCount!==e&&(e===0?this.indices=null:this.indices=this.vertexCount>65535?new Uint32Array(e*3):new Uint16Array(e*3))},_getCubicCurveApproxStep:function(e,t,r,i){var n=fi.dist(e,t)+fi.dist(r,t)+fi.dist(i,r),a=1/(n+1)*this.segmentScale;return a},getCubicCurveVertexCount:function(e,t,r,i){var n=this._getCubicCurveApproxStep(e,t,r,i),a=Math.ceil(1/n);return this.useNativeLine?a*2:a*2+2},getCubicCurveTriangleCount:function(e,t,r,i){var n=this._getCubicCurveApproxStep(e,t,r,i),a=Math.ceil(1/n);return this.useNativeLine?0:a*2},getLineVertexCount:function(){return this.getPolylineVertexCount(Dn)},getLineTriangleCount:function(){return this.getPolylineTriangleCount(Dn)},getPolylineVertexCount:function(e){var t;if(typeof e=="number")t=e;else{var r=typeof e[0]!="number";t=r?e.length:e.length/3}return this.useNativeLine?(t-1)*2:(t-1)*2+2},getPolylineTriangleCount:function(e){var t;if(typeof e=="number")t=e;else{var r=typeof e[0]!="number";t=r?e.length:e.length/3}return this.useNativeLine?0:Math.max(t-1,0)*2},addCubicCurve:function(e,t,r,i,n,a){a==null&&(a=1);for(var o=e[0],s=e[1],l=e[2],u=t[0],f=t[1],h=t[2],d=r[0],c=r[1],v=r[2],p=i[0],m=i[1],_=i[2],x=this._getCubicCurveApproxStep(e,t,r,i),T=x*x,g=T*x,E=3*x,S=3*T,C=6*T,A=6*g,N=o-u*2+d,H=s-f*2+c,R=l-h*2+v,U=(u-d)*3-o+p,V=(f-c)*3-s+m,I=(h-v)*3-l+_,G=o,X=s,q=l,ie=(u-o)*E+N*S+U*g,_e=(f-s)*E+H*S+V*g,we=(h-l)*E+R*S+I*g,ce=N*C+U*A,xe=H*C+V*A,de=R*C+I*A,Ae=U*A,Be=V*A,Oe=I*A,Yt=0,qe=0,Mt=Math.ceil(1/x),Kt=new Float32Array((Mt+1)*3),Kt=[],Xr=0,qe=0;qe<Mt+1;qe++)Kt[Xr++]=G,Kt[Xr++]=X,Kt[Xr++]=q,G+=ie,X+=_e,q+=we,ie+=ce,_e+=xe,we+=de,ce+=Ae,xe+=Be,de+=Oe,Yt+=x,Yt>1&&(G=ie>0?Math.min(G,p):Math.max(G,p),X=_e>0?Math.min(X,m):Math.max(X,m),q=we>0?Math.min(q,_):Math.max(q,_));return this.addPolyline(Kt,n,a)},addLine:function(e,t,r,i){return this.addPolyline([e,t],r,i)},addPolyline:function(e,t,r,i,n){if(e.length){var a=typeof e[0]!="number";if(n==null&&(n=a?e.length:e.length/3),!(n<2)){i==null&&(i=0),r==null&&(r=1),this._itemVertexOffsets.push(this._vertexOffset);var a=typeof e[0]!="number",o=a?typeof t[0]!="number":t.length/4===n,s=this.attributes.position,l=this.attributes.positionPrev,u=this.attributes.positionNext,f=this.attributes.color,h=this.attributes.offset,d=this.indices,c=this._vertexOffset,v,p;r=Math.max(r,.01);for(var m=i;m<n;m++){if(a)v=e[m],o?p=t[m]:p=t;else{var _=m*3;if(v=v||[],v[0]=e[_],v[1]=e[_+1],v[2]=e[_+2],o){var x=m*4;p=p||[],p[0]=t[x],p[1]=t[x+1],p[2]=t[x+2],p[3]=t[x+3]}else p=t}if(this.useNativeLine?m>1&&(s.copy(c,c-1),f.copy(c,c-1),c++):(m<n-1&&(l.set(c+2,v),l.set(c+3,v)),m>0&&(u.set(c-2,v),u.set(c-1,v)),s.set(c,v),s.set(c+1,v),f.set(c,p),f.set(c+1,p),h.set(c,r/2),h.set(c+1,-r/2),c+=2),this.useNativeLine)f.set(c,p),s.set(c,v),c++;else if(m>0){var T=this._triangleOffset*3,d=this.indices;d[T]=c-4,d[T+1]=c-3,d[T+2]=c-2,d[T+3]=c-3,d[T+4]=c-1,d[T+5]=c-2,this._triangleOffset+=2}}if(!this.useNativeLine){var g=this._vertexOffset,E=this._vertexOffset+n*2;l.copy(g,g+2),l.copy(g+1,g+3),u.copy(E-1,E-3),u.copy(E-2,E-4)}return this._vertexOffset=c,this._vertexOffset}}},setItemColor:function(e,t){for(var r=this._itemVertexOffsets[e],i=e<this._itemVertexOffsets.length-1?this._itemVertexOffsets[e+1]:this._vertexOffset,n=r;n<i;n++)this.attributes.color.set(n,t);this.dirty("color")},currentTriangleOffset:function(){return this._triangleOffset},currentVertexOffset:function(){return this._vertexOffset}});Ct(jt.prototype,Gr);const Aa=`@export ecgl.lines3D.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;

attribute vec3 position: POSITION;
attribute vec4 a_Color : COLOR;
varying vec4 v_Color;

void main()
{
 gl_Position = worldViewProjection * vec4(position, 1.0);
 v_Color = a_Color;
}

@end

@export ecgl.lines3D.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

varying vec4 v_Color;

@import clay.util.srgb

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color * v_Color);
#else
 gl_FragColor = color * v_Color;
#endif
}
@end



@export ecgl.lines3D.clipNear

vec4 clipNear(vec4 p1, vec4 p2) {
 float n = (p1.w - near) / (p1.w - p2.w);
 return vec4(mix(p1.xy, p2.xy, n), -near, near);
}

@end

@export ecgl.lines3D.expandLine
#ifdef VERTEX_ANIMATION
 vec4 prevProj = worldViewProjection * vec4(mix(prevPositionPrev, positionPrev, percent), 1.0);
 vec4 currProj = worldViewProjection * vec4(mix(prevPosition, position, percent), 1.0);
 vec4 nextProj = worldViewProjection * vec4(mix(prevPositionNext, positionNext, percent), 1.0);
#else
 vec4 prevProj = worldViewProjection * vec4(positionPrev, 1.0);
 vec4 currProj = worldViewProjection * vec4(position, 1.0);
 vec4 nextProj = worldViewProjection * vec4(positionNext, 1.0);
#endif

 if (currProj.w < 0.0) {
 if (nextProj.w > 0.0) {
 currProj = clipNear(currProj, nextProj);
 }
 else if (prevProj.w > 0.0) {
 currProj = clipNear(currProj, prevProj);
 }
 }

 vec2 prevScreen = (prevProj.xy / abs(prevProj.w) + 1.0) * 0.5 * viewport.zw;
 vec2 currScreen = (currProj.xy / abs(currProj.w) + 1.0) * 0.5 * viewport.zw;
 vec2 nextScreen = (nextProj.xy / abs(nextProj.w) + 1.0) * 0.5 * viewport.zw;

 vec2 dir;
 float len = offset;
 if (position == positionPrev) {
 dir = normalize(nextScreen - currScreen);
 }
 else if (position == positionNext) {
 dir = normalize(currScreen - prevScreen);
 }
 else {
 vec2 dirA = normalize(currScreen - prevScreen);
 vec2 dirB = normalize(nextScreen - currScreen);

 vec2 tanget = normalize(dirA + dirB);

 float miter = 1.0 / max(dot(tanget, dirA), 0.5);
 len *= miter;
 dir = tanget;
 }

 dir = vec2(-dir.y, dir.x) * len;
 currScreen += dir;

 currProj.xy = (currScreen / viewport.zw - 0.5) * 2.0 * abs(currProj.w);
@end


@export ecgl.meshLines3D.vertex

attribute vec3 position: POSITION;
attribute vec3 positionPrev;
attribute vec3 positionNext;
attribute float offset;
attribute vec4 a_Color : COLOR;

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
attribute vec3 prevPositionPrev;
attribute vec3 prevPositionNext;
uniform float percent : 1.0;
#endif

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform vec4 viewport : VIEWPORT;
uniform float near : NEAR;

varying vec4 v_Color;

@import ecgl.common.wireframe.vertexHeader

@import ecgl.lines3D.clipNear

void main()
{
 @import ecgl.lines3D.expandLine

 gl_Position = currProj;

 v_Color = a_Color;

 @import ecgl.common.wireframe.vertexMain
}
@end


@export ecgl.meshLines3D.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];

varying vec4 v_Color;

@import ecgl.common.wireframe.fragmentHeader

@import clay.util.srgb

void main()
{
#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color * v_Color);
#else
 gl_FragColor = color * v_Color;
#endif

 @import ecgl.common.wireframe.fragmentMain
}

@end`,Cl=Li.extend({type:"series.scatter3D",dependencies:["globe","grid3D","geo3D"],visualStyleAccessPath:"itemStyle",hasSymbolVisual:!0,getInitialData:function(e,t){return xa(this)},getFormattedLabel:function(e,t,r,i){var n=qt.getFormattedLabel(this,e,t,r,i);if(n==null){var a=this.getData(),o=a.dimensions[a.dimensions.length-1];n=a.get(o,e)}return n},formatTooltip:function(e){return ya(this,e)},defaultOption:{coordinateSystem:"cartesian3D",zlevel:-10,progressive:1e5,progressiveThreshold:1e5,grid3DIndex:0,globeIndex:0,symbol:"circle",symbolSize:10,blendMode:"source-over",label:{show:!1,position:"right",distance:5,textStyle:{fontSize:14,color:"#000",backgroundColor:"rgba(255,255,255,0.7)",padding:3,borderRadius:3}},itemStyle:{opacity:.8},emphasis:{label:{show:!0}},animationDurationUpdate:500}});function hi(e,i,r){var i=i||document.createElement("canvas");i.width=e,i.height=e;var n=i.getContext("2d");return r&&r(n),i}function Ll(e,t,r,i){$e(t)||(t=[t,t]);var n=Br.getMarginByStyle(r,i),a=t[0]+n.left+n.right,o=t[1]+n.top+n.bottom,s=uo(e,0,0,t[0],t[1]),l=Math.max(a,o);s.x=n.left,s.y=n.top,a>o?s.y+=(l-o)/2:s.x+=(l-a)/2;var u=s.getBoundingRect();return s.x-=u.x,s.y-=u.y,s.setStyle(r),s.update(),s.__size=l,s}function Ml(e,t,r){var i=t.width,n=t.height,a=e.canvas.width,o=e.canvas.height,s=i/a,l=n/o;function u(_){return _<128?1:-1}function f(_,x){var T=1/0;_=Math.floor(_*s),x=Math.floor(x*l);for(var g=x*i+_,E=t.data[g*4],S=u(E),C=Math.max(x-r,0);C<Math.min(x+r,n);C++)for(var A=Math.max(_-r,0);A<Math.min(_+r,i);A++){var g=C*i+A,N=t.data[g*4],H=u(N),R=A-_,U=C-x;if(S!==H){var V=R*R+U*U;V<T&&(T=V)}}return S*Math.sqrt(T)}for(var h=e.createImageData(a,o),d=0;d<o;d++)for(var c=0;c<a;c++){var v=f(c,d),p=v/r*.5+.5,m=(d*a+c)*4;h.data[m++]=(1-p)*255,h.data[m++]=(1-p)*255,h.data[m++]=(1-p)*255,h.data[m++]=255}return h}var Br={getMarginByStyle:function(e){var t=e.minMargin||0,r=0;e.stroke&&e.stroke!=="none"&&(r=e.lineWidth==null?1:e.lineWidth);var i=e.shadowBlur||0,n=e.shadowOffsetX||0,a=e.shadowOffsetY||0,o={};return o.left=Math.max(r/2,-n+i,t),o.right=Math.max(r/2,n+i,t),o.top=Math.max(r/2,-a+i,t),o.bottom=Math.max(r/2,a+i,t),o},createSymbolSprite:function(e,t,r,i){var n=Ll(e,t,r),a=Br.getMarginByStyle(r);return{image:hi(n.__size,i,function(o){$n(o,n)}),margin:a}},createSDFFromCanvas:function(e,t,r,i){return hi(t,i,function(n){var a=e.getContext("2d"),o=a.getImageData(0,0,e.width,e.height);n.putImageData(Ml(n,o,r),0,0)})},createSimpleSprite:function(e,t){return hi(e,t,function(r){var i=e/2;r.beginPath(),r.arc(i,i,60,0,Math.PI*2,!1),r.closePath();var n=r.createRadialGradient(i,i,0,i,i,i);n.addColorStop(0,"rgba(255, 255, 255, 1)"),n.addColorStop(.5,"rgba(255, 255, 255, 0.5)"),n.addColorStop(1,"rgba(255, 255, 255, 0)"),r.fillStyle=n,r.fill()})}},Pn=Fe.vec3;const Dl={needsSortVertices:function(){return this.sortVertices},needsSortVerticesProgressively:function(){return this.needsSortVertices()&&this.vertexCount>=2e4},doSortVertices:function(e,t){var r=this.indices,i=Pn.create();if(!r){r=this.indices=this.vertexCount>65535?new Uint32Array(this.vertexCount):new Uint16Array(this.vertexCount);for(var n=0;n<r.length;n++)r[n]=n}if(t===0){var a=this.attributes.position,e=e.array,o=0;(!this._zList||this._zList.length!==this.vertexCount)&&(this._zList=new Float32Array(this.vertexCount));for(var s,n=0;n<this.vertexCount;n++){a.get(n,i);var l=Pn.sqrDist(i,e);isNaN(l)&&(l=1e7,o++),n===0?(s=l,l=0):l=l-s,this._zList[n]=l}this._noneCount=o}if(this.vertexCount<2e4)t===0&&this._simpleSort(this._noneCount/this.vertexCount>.05);else for(var n=0;n<3;n++)this._progressiveQuickSort(t*3+n);this.dirtyIndices()},_simpleSort:function(e){var t=this._zList,r=this.indices;function i(n,a){return t[a]-t[n]}e?Array.prototype.sort.call(r,i):Wt.sort(r,i,0,r.length-1)},_progressiveQuickSort:function(e){var t=this._zList,r=this.indices;this._quickSort=this._quickSort||new Wt,this._quickSort.step(r,function(i,n){return t[n]-t[i]},e)}},Pl=`@export ecgl.sdfSprite.vertex

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform float elapsedTime : 0;

attribute vec3 position : POSITION;

#ifdef VERTEX_SIZE
attribute float size;
#else
uniform float u_Size;
#endif

#ifdef VERTEX_COLOR
attribute vec4 a_FillColor: COLOR;
varying vec4 v_Color;
#endif

#ifdef VERTEX_ANIMATION
attribute vec3 prevPosition;
attribute float prevSize;
uniform float percent : 1.0;
#endif


#ifdef POSITIONTEXTURE_ENABLED
uniform sampler2D positionTexture;
#endif

varying float v_Size;

void main()
{

#ifdef POSITIONTEXTURE_ENABLED
 gl_Position = worldViewProjection * vec4(texture2D(positionTexture, position.xy).xy, -10.0, 1.0);
#else

 #ifdef VERTEX_ANIMATION
 vec3 pos = mix(prevPosition, position, percent);
 #else
 vec3 pos = position;
 #endif
 gl_Position = worldViewProjection * vec4(pos, 1.0);
#endif

#ifdef VERTEX_SIZE
#ifdef VERTEX_ANIMATION
 v_Size = mix(prevSize, size, percent);
#else
 v_Size = size;
#endif
#else
 v_Size = u_Size;
#endif

#ifdef VERTEX_COLOR
 v_Color = a_FillColor;
 #endif

 gl_PointSize = v_Size;
}

@end

@export ecgl.sdfSprite.fragment

uniform vec4 color: [1, 1, 1, 1];
uniform vec4 strokeColor: [1, 1, 1, 1];
uniform float smoothing: 0.07;

uniform float lineWidth: 0.0;

#ifdef VERTEX_COLOR
varying vec4 v_Color;
#endif

varying float v_Size;

uniform sampler2D sprite;

@import clay.util.srgb

void main()
{
 gl_FragColor = color;

 vec4 _strokeColor = strokeColor;

#ifdef VERTEX_COLOR
 gl_FragColor *= v_Color;
 #endif

#ifdef SPRITE_ENABLED
 float d = texture2D(sprite, gl_PointCoord).r;
 gl_FragColor.a *= smoothstep(0.5 - smoothing, 0.5 + smoothing, d);

 if (lineWidth > 0.0) {
 float sLineWidth = lineWidth / 2.0;

 float outlineMaxValue0 = 0.5 + sLineWidth;
 float outlineMaxValue1 = 0.5 + sLineWidth + smoothing;
 float outlineMinValue0 = 0.5 - sLineWidth - smoothing;
 float outlineMinValue1 = 0.5 - sLineWidth;

 if (d <= outlineMaxValue1 && d >= outlineMinValue0) {
 float a = _strokeColor.a;
 if (d <= outlineMinValue1) {
 a = a * smoothstep(outlineMinValue0, outlineMinValue1, d);
 }
 else {
 a = a * smoothstep(outlineMaxValue1, outlineMaxValue0, d);
 }
 gl_FragColor.rgb = mix(gl_FragColor.rgb * gl_FragColor.a, _strokeColor.rgb, a);
 gl_FragColor.a = gl_FragColor.a * (1.0 - a) + a;
 }
 }
#endif

#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(gl_FragColor);
#endif
}
@end`;var ci=Fe.vec4;w.Shader.import(Pl);var Nl=w.Mesh.extend(function(){var e=new w.Geometry({dynamic:!0,attributes:{color:new w.Geometry.Attribute("color","float",4,"COLOR"),position:new w.Geometry.Attribute("position","float",3,"POSITION"),size:new w.Geometry.Attribute("size","float",1),prevPosition:new w.Geometry.Attribute("prevPosition","float",3),prevSize:new w.Geometry.Attribute("prevSize","float",1)}});Object.assign(e,Dl);var t=new w.Material({shader:w.createShader("ecgl.sdfSprite"),transparent:!0,depthMask:!1});t.enableTexture("sprite"),t.define("both","VERTEX_COLOR"),t.define("both","VERTEX_SIZE");var r=new w.Texture2D({image:document.createElement("canvas"),flipY:!1});return t.set("sprite",r),e.pick=this._pick.bind(this),{geometry:e,material:t,mode:w.Mesh.POINTS,sizeScale:1}},{_pick:function(e,t,r,i,n,a){var o=this._positionNDC;if(o)for(var s=r.viewport,l=2/s.width,u=2/s.height,f=this.geometry.vertexCount-1;f>=0;f--){var h;this.geometry.indices?h=this.geometry.indices[f]:h=f;var d=o[h*2],c=o[h*2+1],v=this.geometry.attributes.size.get(h)/this.sizeScale,p=v/2;if(e>d-p*l&&e<d+p*l&&t>c-p*u&&t<c+p*u){var m=new w.Vector3,_=new w.Vector3;this.geometry.attributes.position.get(h,m.array),w.Vector3.transformMat4(_,m,this.worldTransform),a.push({vertexIndex:h,point:m,pointWorld:_,target:this,distance:_.distance(i.getWorldPosition())})}}},updateNDCPosition:function(e,t,r){var i=this._positionNDC,n=this.geometry;(!i||i.length/2!==n.vertexCount)&&(i=this._positionNDC=new Float32Array(n.vertexCount*2));for(var a=ci.create(),o=0;o<n.vertexCount;o++)n.attributes.position.get(o,a),a[3]=1,ci.transformMat4(a,a,e.array),ci.scale(a,a,1/a[3]),i[o*2]=a[0],i[o*2+1]=a[1]}}),Nn=20,Rn=-10;function Rl(e,t){return e&&t&&e[0]===t[0]&&e[1]===t[1]}function Fr(e,t){this.rootNode=new w.Node,this.is2D=e,this._labelsBuilder=new pt(256,256,t),this._labelsBuilder.getMesh().renderOrder=100,this.rootNode.add(this._labelsBuilder.getMesh()),this._api=t,this._spriteImageCanvas=document.createElement("canvas"),this._startDataIndex=0,this._endDataIndex=0,this._sizeScale=1}Fr.prototype={constructor:Fr,highlightOnMouseover:!0,update:function(e,t,r,i,n){var a=this._prevMesh;this._prevMesh=this._mesh,this._mesh=a;var o=e.getData();if(i==null&&(i=0),n==null&&(n=o.count()),this._startDataIndex=i,this._endDataIndex=n-1,!this._mesh){var s=this._prevMesh&&this._prevMesh.material;this._mesh=new Nl({renderOrder:10,frustumCulling:!1}),s&&(this._mesh.material=s)}var s=this._mesh.material,l=this._mesh.geometry,u=l.attributes;this.rootNode.remove(this._prevMesh),this.rootNode.add(this._mesh),this._setPositionTextureToMesh(this._mesh,this._positionTexture);var f=this._getSymbolInfo(e,i,n),h=r.getDevicePixelRatio(),d=e.getModel("itemStyle").getItemStyle(),c=e.get("large"),v=1;f.maxSize>2?(v=this._updateSymbolSprite(e,d,f,h),s.enableTexture("sprite")):s.disableTexture("sprite"),u.position.init(n-i);var p=[];if(c){s.undefine("VERTEX_SIZE"),s.undefine("VERTEX_COLOR");var m=yl(o),_=xl(o);w.parseColor(m,p),p[3]*=_,s.set({color:p,u_Size:f.maxSize*this._sizeScale})}else s.set({color:[1,1,1,1]}),s.define("VERTEX_SIZE"),s.define("VERTEX_COLOR"),u.size.init(n-i),u.color.init(n-i),this._originalOpacity=new Float32Array(n-i);for(var x=o.getLayout("points"),T=u.position.value,g=0;g<n-i;g++){var E=g*3,S=g*2;if(this.is2D?(T[E]=x[S],T[E+1]=x[S+1],T[E+2]=Rn):(T[E]=x[E],T[E+1]=x[E+1],T[E+2]=x[E+2]),!c){var m=Je(o,g),_=nt(o,g);w.parseColor(m,p),p[3]*=_,u.color.set(g,p),p[3]<.99;var C=o.getItemVisual(g,"symbolSize");C=C instanceof Array?Math.max(C[0],C[1]):C,isNaN(C)&&(C=0),u.size.value[g]=C*v*this._sizeScale,this._originalOpacity[g]=p[3]}}this._mesh.sizeScale=v,l.updateBoundingBox(),l.dirty(),this._updateMaterial(e,d);var A=e.coordinateSystem;if(A&&A.viewGL){var N=A.viewGL.isLinearSpace()?"define":"undefine";s[N]("fragment","SRGB_DECODE")}c||this._updateLabelBuilder(e,i,n),this._updateHandler(e,t,r),this._updateAnimation(e),this._api=r},getPointsMesh:function(){return this._mesh},updateLabels:function(e){this._labelsBuilder.updateLabels(e)},hideLabels:function(){this.rootNode.remove(this._labelsBuilder.getMesh())},showLabels:function(){this.rootNode.add(this._labelsBuilder.getMesh())},dispose:function(){this._labelsBuilder.dispose()},_updateSymbolSprite:function(e,t,r,i){r.maxSize=Math.min(r.maxSize*2,200);var n=[];return r.aspect>1?(n[0]=r.maxSize,n[1]=r.maxSize/r.aspect):(n[1]=r.maxSize,n[0]=r.maxSize*r.aspect),n[0]=n[0]||1,n[1]=n[1]||1,(this._symbolType!==r.type||!Rl(this._symbolSize,n)||this._lineWidth!==t.lineWidth)&&(Br.createSymbolSprite(r.type,n,{fill:"#fff",lineWidth:t.lineWidth,stroke:"transparent",shadowColor:"transparent",minMargin:Math.min(n[0]/2,10)},this._spriteImageCanvas),Br.createSDFFromCanvas(this._spriteImageCanvas,Math.min(this._spriteImageCanvas.width,32),Nn,this._mesh.material.get("sprite").image),this._symbolType=r.type,this._symbolSize=n,this._lineWidth=t.lineWidth),this._spriteImageCanvas.width/r.maxSize*i},_updateMaterial:function(e,t){var r=e.get("blendMode")==="lighter"?w.additiveBlend:null,i=this._mesh.material;i.blend=r,i.set("lineWidth",t.lineWidth/Nn);var n=w.parseColor(t.stroke);i.set("strokeColor",n),i.transparent=!0,i.depthMask=!1,i.depthTest=!this.is2D,i.sortVertices=!this.is2D},_updateLabelBuilder:function(e,o,r){var i=e.getData(),n=this._mesh.geometry,a=n.attributes.position.value,o=this._startDataIndex,s=this._mesh.sizeScale;this._labelsBuilder.updateData(i,o,r),this._labelsBuilder.getLabelPosition=function(l,u,f){var h=(l-o)*3;return[a[h],a[h+1],a[h+2]]},this._labelsBuilder.getLabelDistance=function(l,u,f){var h=n.attributes.size.get(l-o)/s;return h/2+f},this._labelsBuilder.updateLabels()},_updateAnimation:function(e){w.updateVertexAnimation([["prevPosition","position"],["prevSize","size"]],this._prevMesh,this._mesh,e)},_updateHandler:function(e,t,r){var i=e.getData(),n=this._mesh,a=this,o=-1,s=e.coordinateSystem&&e.coordinateSystem.type==="cartesian3D",l;s&&(l=e.coordinateSystem.model),n.seriesIndex=e.seriesIndex,n.off("mousemove"),n.off("mouseout"),n.on("mousemove",function(u){var f=u.vertexIndex+a._startDataIndex;f!==o&&(this.highlightOnMouseover&&(this.downplay(i,o),this.highlight(i,f),this._labelsBuilder.updateLabels([f])),s&&r.dispatchAction({type:"grid3DShowAxisPointer",value:[i.get(e.coordDimToDataDim("x")[0],f),i.get(e.coordDimToDataDim("y")[0],f),i.get(e.coordDimToDataDim("z")[0],f)],grid3DIndex:l.componentIndex})),n.dataIndex=f,o=f},this),n.on("mouseout",function(u){var f=u.vertexIndex+a._startDataIndex;this.highlightOnMouseover&&(this.downplay(i,f),this._labelsBuilder.updateLabels()),o=-1,n.dataIndex=-1,s&&r.dispatchAction({type:"grid3DHideAxisPointer",grid3DIndex:l.componentIndex})},this)},updateLayout:function(e,t,r){var i=e.getData();if(this._mesh){var n=this._mesh.geometry.attributes.position.value,a=i.getLayout("points");if(this.is2D)for(var o=0;o<a.length/2;o++){var s=o*3,l=o*2;n[s]=a[l],n[s+1]=a[l+1],n[s+2]=Rn}else for(var o=0;o<a.length;o++)n[o]=a[o];this._mesh.geometry.dirty(),r.getZr().refresh()}},updateView:function(e){if(this._mesh){var t=new F;F.mul(t,e.viewMatrix,this._mesh.worldTransform),F.mul(t,e.projectionMatrix,t),this._mesh.updateNDCPosition(t,this.is2D,this._api)}},highlight:function(e,t){if(!(t>this._endDataIndex||t<this._startDataIndex)){var r=e.getItemModel(t),i=r.getModel("emphasis.itemStyle"),n=i.get("color"),a=i.get("opacity");if(n==null){var o=Je(e,t);n=Jn(o,-.4)}a==null&&(a=nt(e,t));var s=w.parseColor(n);s[3]*=a,this._mesh.geometry.attributes.color.set(t-this._startDataIndex,s),this._mesh.geometry.dirtyAttribute("color"),this._api.getZr().refresh()}},downplay:function(e,t){if(!(t>this._endDataIndex||t<this._startDataIndex)){var r=Je(e,t),i=nt(e,t),n=w.parseColor(r);n[3]*=i,this._mesh.geometry.attributes.color.set(t-this._startDataIndex,n),this._mesh.geometry.dirtyAttribute("color"),this._api.getZr().refresh()}},fadeOutAll:function(e){if(this._originalOpacity){for(var t=this._mesh.geometry,r=0;r<t.vertexCount;r++){var i=this._originalOpacity[r]*e;t.attributes.color.value[r*4+3]=i}t.dirtyAttribute("color"),this._api.getZr().refresh()}},fadeInAll:function(){this.fadeOutAll(1)},setPositionTexture:function(e){this._mesh&&this._setPositionTextureToMesh(this._mesh,e),this._positionTexture=e},removePositionTexture:function(){this._positionTexture=null,this._mesh&&this._setPositionTextureToMesh(this._mesh,null)},setSizeScale:function(e){if(e!==this._sizeScale){if(this._mesh){var t=this._mesh.material.get("u_Size");this._mesh.material.set("u_Size",t/this._sizeScale*e);var r=this._mesh.geometry.attributes;if(r.size.value)for(var i=0;i<r.size.value.length;i++)r.size.value[i]=r.size.value[i]/this._sizeScale*e}this._sizeScale=e}},_setPositionTextureToMesh:function(e,t){t&&e.material.set("positionTexture",t),e.material[t?"enableTexture":"disableTexture"]("positionTexture")},_getSymbolInfo:function(e,t,r){if(e.get("large")){var i=Ce.firstNotNull(e.get("symbolSize"),1),s,a;return i instanceof Array?(s=Math.max(i[0],i[1]),a=i[0]/i[1]):(s=i,a=1),{maxSize:i,type:e.get("symbol"),aspect:a}}for(var n=e.getData(),a,o=n.getItemVisual(0,"symbol")||"circle",s=0,l=t;l<r;l++){var i=n.getItemVisual(l,"symbolSize"),u=n.getItemVisual(l,"symbol"),f;if(i instanceof Array)f=i[0]/i[1],s=Math.max(Math.max(i[0],i[1]),s);else{if(isNaN(i))continue;f=1,s=Math.max(i,s)}o=u,a=f}return{maxSize:s,type:o,aspect:a}}};const Ol=Mi.extend({type:"scatter3D",hasSymbolVisual:!0,__ecgl__:!0,init:function(e,t){this.groupGL=new w.Node,this._pointsBuilderList=[],this._currentStep=0},render:function(e,t,r){if(this.groupGL.removeAll(),!!e.getData().count()){var i=e.coordinateSystem;if(i&&i.viewGL){i.viewGL.add(this.groupGL),this._camera=i.viewGL.camera;var n=this._pointsBuilderList[0];n||(n=this._pointsBuilderList[0]=new Fr(!1,r)),this._pointsBuilderList.length=1,this.groupGL.add(n.rootNode),n.update(e,t,r),n.updateView(i.viewGL.camera)}}},incrementalPrepareRender:function(e,t,r){var i=e.coordinateSystem;i&&i.viewGL&&(i.viewGL.add(this.groupGL),this._camera=i.viewGL.camera),this.groupGL.removeAll(),this._currentStep=0},incrementalRender:function(e,t,r,i){if(!(e.end<=e.start)){var n=this._pointsBuilderList[this._currentStep];n||(n=new Fr(!1,i),this._pointsBuilderList[this._currentStep]=n),this.groupGL.add(n.rootNode),n.update(t,r,i,e.start,e.end),n.updateView(t.coordinateSystem.viewGL.camera),this._currentStep++}},updateCamera:function(){this._pointsBuilderList.forEach(function(e){e.updateView(this._camera)},this)},highlight:function(e,t,r,i){this._toggleStatus("highlight",e,t,r,i)},downplay:function(e,t,r,i){this._toggleStatus("downplay",e,t,r,i)},_toggleStatus:function(e,t,r,i,n){var a=t.getData(),o=Ce.queryDataIndex(a,n),s=e==="highlight";o!=null?bt(qt.normalizeToArray(o),function(l){for(var u=0;u<this._pointsBuilderList.length;u++){var f=this._pointsBuilderList[u];s?f.highlight(a,l):f.downplay(a,l)}},this):a.each(function(l){for(var u=0;u<this._pointsBuilderList.length;u++){var f=this._pointsBuilderList[u];s?f.highlight(a,l):f.downplay(a,l)}})},dispose:function(){this._pointsBuilderList.forEach(function(e){e.dispose()}),this.groupGL.removeAll()},remove:function(){this.groupGL.removeAll()}});function Bu(e){e.registerChartView(Ol),e.registerSeriesModel(Cl),e.registerLayout({seriesType:"scatter3D",reset:function(t){var r=t.coordinateSystem;if(r){var i=r.dimensions;if(i.length<3)return;var n=i.map(function(s){return t.coordDimToDataDim(s)[0]}),a=[],o=[];return{progress:function(s,l){for(var u=new Float32Array((s.end-s.start)*3),f=s.start;f<s.end;f++){var h=(f-s.start)*3;a[0]=l.get(n[0],f),a[1]=l.get(n[1],f),a[2]=l.get(n[2],f),r.dataToPoint(a,o),u[h]=o[0],u[h+1]=o[1],u[h+2]=o[2]}l.setLayout("points",u)}}}}})}var ve=Fe.vec3,On=Fe.vec2,tt=ve.normalize,Ar=ve.cross,In=ve.sub,di=ve.add,dt=ve.create,ut=dt(),Ue=dt(),ft=dt(),rr=dt(),Bn=[],Fn=[];function Il(e,t){On.copy(Bn,e[0]),On.copy(Fn,e[1]);var r=[],i=r[0]=dt(),n=r[1]=dt(),a=r[2]=dt(),o=r[3]=dt();t.dataToPoint(Bn,i),t.dataToPoint(Fn,o),tt(ut,i),In(Ue,o,i),tt(Ue,Ue),Ar(ft,Ue,ut),tt(ft,ft),Ar(Ue,ut,ft),di(n,ut,Ue),tt(n,n),tt(ut,o),In(Ue,i,o),tt(Ue,Ue),Ar(ft,Ue,ut),tt(ft,ft),Ar(Ue,ut,ft),di(a,ut,Ue),tt(a,a),di(rr,i,o),tt(rr,rr);var s=ve.dot(i,rr),l=ve.dot(rr,n),u=(Math.max(ve.len(i),ve.len(o))-s)/l*2;return ve.scaleAndAdd(n,i,n,u),ve.scaleAndAdd(a,o,a,u),r}function Bl(e,t,r){var i=[],n=i[0]=ve.create(),a=i[1]=ve.create(),o=i[2]=ve.create(),s=i[3]=ve.create();t.dataToPoint(e[0],n),t.dataToPoint(e[1],s);var l=ve.dist(n,s);return ve.lerp(a,n,s,.3),ve.lerp(o,n,s,.3),ve.scaleAndAdd(a,a,r,Math.min(l*.1,10)),ve.scaleAndAdd(o,o,r,Math.min(l*.1,10)),i}function Ca(e,t){for(var r=new Float32Array(e.length*3),i=0,n=[],a=0;a<e.length;a++)t.dataToPoint(e[a],n),r[i++]=n[0],r[i++]=n[1],r[i++]=n[2];return r}function La(e){var t=[];return e.each(function(r){var i=e.getItemModel(r),n=i.option instanceof Array?i.option:i.getShallow("coords",!0);t.push(n)}),{coordsList:t}}function Fl(e,t){var r=e.getData(),i=e.get("polyline");r.setLayout("lineType",i?"polyline":"cubicBezier");var n=La(r);r.each(function(a){var o=n.coordsList[a],s=i?Ca:Il;r.setItemLayout(a,s(o,t))})}function Un(e,t,r){var i=e.getData(),n=e.get("polyline"),a=La(i);i.setLayout("lineType",n?"polyline":"cubicBezier"),i.each(function(o){var s=a.coordsList[o],l=n?Ca(s,t):Bl(s,t,r);i.setItemLayout(o,l)})}function Ul(e,t){e.eachSeriesByType("lines3D",function(r){var i=r.coordinateSystem;i.type==="globe"?Fl(r,i):i.type==="geo3D"?Un(r,i,[0,1,0]):(i.type==="mapbox3D"||i.type==="maptalks3D")&&Un(r,i,[0,0,1])})}const zl=Li.extend({type:"series.lines3D",dependencies:["globe"],visualStyleAccessPath:"lineStyle",visualDrawType:"stroke",getInitialData:function(e,t){var r=new Qn(["value"],this);return r.hasItemOption=!1,r.initData(e.data,[],function(i,n,a,o){if(i instanceof Array)return NaN;r.hasItemOption=!0;var s=i.value;if(s!=null)return s instanceof Array?s[o]:s}),r},defaultOption:{coordinateSystem:"globe",globeIndex:0,geo3DIndex:0,zlevel:-10,polyline:!1,effect:{show:!1,period:4,trailWidth:4,trailLength:.2,spotIntensity:6},silent:!0,blendMode:"source-over",lineStyle:{width:1,opacity:.5}}}),Hl=`@export ecgl.trail2.vertex
attribute vec3 position: POSITION;
attribute vec3 positionPrev;
attribute vec3 positionNext;
attribute float offset;
attribute float dist;
attribute float distAll;
attribute float start;

attribute vec4 a_Color : COLOR;

uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform vec4 viewport : VIEWPORT;
uniform float near : NEAR;

uniform float speed : 0;
uniform float trailLength: 0.3;
uniform float time;
uniform float period: 1000;

uniform float spotSize: 1;

varying vec4 v_Color;
varying float v_Percent;
varying float v_SpotPercent;

@import ecgl.common.wireframe.vertexHeader

@import ecgl.lines3D.clipNear

void main()
{
 @import ecgl.lines3D.expandLine

 gl_Position = currProj;

 v_Color = a_Color;

 @import ecgl.common.wireframe.vertexMain

#ifdef CONSTANT_SPEED
 float t = mod((speed * time + start) / distAll, 1. + trailLength) - trailLength;
#else
 float t = mod((time + start) / period, 1. + trailLength) - trailLength;
#endif

 float trailLen = distAll * trailLength;

 v_Percent = (dist - t * distAll) / trailLen;

 v_SpotPercent = spotSize / distAll;

 }
@end


@export ecgl.trail2.fragment

uniform vec4 color : [1.0, 1.0, 1.0, 1.0];
uniform float spotIntensity: 5;

varying vec4 v_Color;
varying float v_Percent;
varying float v_SpotPercent;

@import ecgl.common.wireframe.fragmentHeader

@import clay.util.srgb

void main()
{
 if (v_Percent > 1.0 || v_Percent < 0.0) {
 discard;
 }

 float fade = v_Percent;

#ifdef SRGB_DECODE
 gl_FragColor = sRGBToLinear(color * v_Color);
#else
 gl_FragColor = color * v_Color;
#endif

 @import ecgl.common.wireframe.fragmentMain

 if (v_Percent > (1.0 - v_SpotPercent)) {
 gl_FragColor.rgb *= spotIntensity;
 }

 gl_FragColor.a *= fade;
}

@end`;var zn=Fe.vec3;function Vl(e){return e>0?1:-1}w.Shader.import(Hl);const Gl=w.Mesh.extend(function(){var e=new w.Material({shader:new w.Shader(w.Shader.source("ecgl.trail2.vertex"),w.Shader.source("ecgl.trail2.fragment")),transparent:!0,depthMask:!1}),t=new jt({dynamic:!0});return t.createAttribute("dist","float",1),t.createAttribute("distAll","float",1),t.createAttribute("start","float",1),{geometry:t,material:e,culling:!1,$ignorePicking:!0}},{updateData:function(e,t,r){var i=e.hostModel,n=this.geometry,a=i.getModel("effect"),o=a.get("trailWidth")*t.getDevicePixelRatio(),s=a.get("trailLength"),l=i.get("effect.constantSpeed"),u=i.get("effect.period")*1e3,f=l!=null;f?this.material.set("speed",l/1e3):this.material.set("period",u),this.material[f?"define":"undefine"]("vertex","CONSTANT_SPEED");var h=i.get("polyline");n.trailLength=s,this.material.set("trailLength",s),n.resetOffset(),["position","positionPrev","positionNext"].forEach(function(C){n.attributes[C].value=r.attributes[C].value});var d=["dist","distAll","start","offset","color"];d.forEach(function(C){n.attributes[C].init(n.vertexCount)}),n.indices=r.indices;var c=[],v=a.get("trailColor"),p=a.get("trailOpacity"),m=v!=null,_=p!=null;this.updateWorldTransform();var x=this.worldTransform.x.len(),T=this.worldTransform.y.len(),g=this.worldTransform.z.len(),E=0,S=0;e.each(function(C){var A=e.getItemLayout(C),N=_?p:nt(e,C),H=Je(e,C);N==null&&(N=1),c=w.parseColor(m?v:H,c),c[3]*=N;for(var R=h?r.getPolylineVertexCount(A):r.getCubicCurveVertexCount(A[0],A[1],A[2],A[3]),U=0,V=[],I=[],G=E;G<E+R;G++)n.attributes.position.get(G,V),V[0]*=x,V[1]*=T,V[2]*=g,G>E&&(U+=zn.dist(V,I)),n.attributes.dist.set(G,U),zn.copy(I,V);S=Math.max(S,U);for(var X=Math.random()*(f?U:u),G=E;G<E+R;G++)n.attributes.distAll.set(G,U),n.attributes.start.set(G,X),n.attributes.offset.set(G,Vl(r.attributes.offset.get(G))*o/2),n.attributes.color.set(G,c);E+=R}),this.material.set("spotSize",S*.1*s),this.material.set("spotIntensity",a.get("spotIntensity")),n.dirty()},setAnimationTime:function(e){this.material.set("time",e)}});w.Shader.import(Aa);function kl(e){return e.radius!=null?e.radius:e.size!=null?Math.max(e.size[0],e.size[1],e.size[2]):100}const Wl=Mi.extend({type:"lines3D",__ecgl__:!0,init:function(e,t){this.groupGL=new w.Node,this._meshLinesMaterial=new w.Material({shader:w.createShader("ecgl.meshLines3D"),transparent:!0,depthMask:!1}),this._linesMesh=new w.Mesh({geometry:new jt,material:this._meshLinesMaterial,$ignorePicking:!0}),this._trailMesh=new Gl},render:function(e,t,r){this.groupGL.add(this._linesMesh);var i=e.coordinateSystem,n=e.getData();if(i&&i.viewGL){var a=i.viewGL;a.add(this.groupGL),this._updateLines(e,t,r);var o=i.viewGL.isLinearSpace()?"define":"undefine";this._linesMesh.material[o]("fragment","SRGB_DECODE"),this._trailMesh.material[o]("fragment","SRGB_DECODE")}var s=this._trailMesh;if(s.stopAnimation(),e.get("effect.show")){this.groupGL.add(s),s.updateData(n,r,this._linesMesh.geometry),s.__time=s.__time||0;var l=3600*1e3;this._curveEffectsAnimator=s.animate("",{loop:!0}).when(l,{__time:l}).during(function(){s.setAnimationTime(s.__time)}).start()}else this.groupGL.remove(s),this._curveEffectsAnimator=null;this._linesMesh.material.blend=this._trailMesh.material.blend=e.get("blendMode")==="lighter"?w.additiveBlend:null},pauseEffect:function(){this._curveEffectsAnimator&&this._curveEffectsAnimator.pause()},resumeEffect:function(){this._curveEffectsAnimator&&this._curveEffectsAnimator.resume()},toggleEffect:function(){var e=this._curveEffectsAnimator;e&&(e.isPaused()?e.resume():e.pause())},_updateLines:function(e,t,r){var i=e.getData(),n=e.coordinateSystem,a=this._linesMesh.geometry,o=e.get("polyline");a.expandLine=!0;var s=kl(n);a.segmentScale=s/20;var l="lineStyle.width".split("."),u=r.getDevicePixelRatio();i.each(function(c){var v=i.getItemModel(c),p=v.get(l);p==null&&(p=1),i.setItemVisual(c,"lineWidth",p)}),a.useNativeLine=!1;var f=0,h=0;i.each(function(c){var v=i.getItemLayout(c);o?(f+=a.getPolylineVertexCount(v),h+=a.getPolylineTriangleCount(v)):(f+=a.getCubicCurveVertexCount(v[0],v[1],v[2],v[3]),h+=a.getCubicCurveTriangleCount(v[0],v[1],v[2],v[3]))}),a.setVertexCount(f),a.setTriangleCount(h),a.resetOffset();var d=[];i.each(function(c){var v=i.getItemLayout(c),p=Je(i,c),m=nt(i,c),_=i.getItemVisual(c,"lineWidth")*u;m==null&&(m=1),d=w.parseColor(p,d),d[3]*=m,o?a.addPolyline(v,d,_):a.addCubicCurve(v[0],v[1],v[2],v[3],d,_)}),a.dirty()},remove:function(){this.groupGL.removeAll()},dispose:function(){this.groupGL.removeAll()}});function Fu(e){e.registerChartView(Wl),e.registerSeriesModel(zl),e.registerLayout(Ul),e.registerAction({type:"lines3DPauseEffect",event:"lines3deffectpaused",update:"series.lines3D:pauseEffect"},function(){}),e.registerAction({type:"lines3DResumeEffect",event:"lines3deffectresumed",update:"series.lines3D:resumeEffect"},function(){}),e.registerAction({type:"lines3DToggleEffect",event:"lines3deffectchanged",update:"series.lines3D:toggleEffect"},function(){})}const Xl={defaultOption:{viewControl:{projection:"perspective",autoRotate:!1,autoRotateDirection:"cw",autoRotateSpeed:10,autoRotateAfterStill:3,damping:.8,rotateSensitivity:1,zoomSensitivity:1,panSensitivity:1,panMouseButton:"middle",rotateMouseButton:"left",distance:150,minDistance:40,maxDistance:400,orthographicSize:150,maxOrthographicSize:400,minOrthographicSize:20,center:[0,0,0],alpha:0,beta:0,minAlpha:-90,maxAlpha:90}},setView:function(e){e=e||{},this.option.viewControl=this.option.viewControl||{},e.alpha!=null&&(this.option.viewControl.alpha=e.alpha),e.beta!=null&&(this.option.viewControl.beta=e.beta),e.distance!=null&&(this.option.viewControl.distance=e.distance),e.center!=null&&(this.option.viewControl.center=e.center)}},ql={defaultOption:{postEffect:{enable:!1,bloom:{enable:!0,intensity:.1},depthOfField:{enable:!1,focalRange:20,focalDistance:50,blurRadius:10,fstop:2.8,quality:"medium"},screenSpaceAmbientOcclusion:{enable:!1,radius:2,quality:"medium",intensity:1},screenSpaceReflection:{enable:!1,quality:"medium",maxRoughness:.8},colorCorrection:{enable:!0,exposure:0,brightness:0,contrast:1,saturation:1,lookupTexture:""},edge:{enable:!1},FXAA:{enable:!1}},temporalSuperSampling:{enable:"auto"}}},jl={defaultOption:{light:{main:{shadow:!1,shadowQuality:"high",color:"#fff",intensity:1,alpha:0,beta:0},ambient:{color:"#fff",intensity:.2},ambientCubemap:{texture:null,exposure:1,diffuseIntensity:.5,specularIntensity:.5}}}};var Ur=function(){this._pool={},this._allocatedTextures=[]};Ur.prototype={constructor:Ur,get:function(e){var t=Hn(e);this._pool.hasOwnProperty(t)||(this._pool[t]=[]);var r=this._pool[t];if(!r.length){var i=new K(e);return this._allocatedTextures.push(i),i}return r.pop()},put:function(e){var t=Hn(e);this._pool.hasOwnProperty(t)||(this._pool[t]=[]);var r=this._pool[t];r.push(e)},clear:function(e){for(var t=0;t<this._allocatedTextures.length;t++)this._allocatedTextures[t].dispose(e);this._pool={},this._allocatedTextures=[]}};var Ma={width:512,height:512,type:L.UNSIGNED_BYTE,format:L.RGBA,wrapS:L.CLAMP_TO_EDGE,wrapT:L.CLAMP_TO_EDGE,minFilter:L.LINEAR_MIPMAP_LINEAR,magFilter:L.LINEAR,useMipmap:!0,anisotropic:1,flipY:!0,unpackAlignment:4,premultiplyAlpha:!1},vi=Object.keys(Ma);function Hn(e){he.defaultsWithPropList(e,Ma,vi),Zl(e);for(var t="",r=0;r<vi.length;r++){var i=vi[r],n=e[i].toString();t+=n}return t}function Zl(e){var t=Yl(e.width,e.height);e.format===L.DEPTH_COMPONENT&&(e.useMipmap=!1),(!t||!e.useMipmap)&&(e.minFilter==L.NEAREST_MIPMAP_NEAREST||e.minFilter==L.NEAREST_MIPMAP_LINEAR?e.minFilter=L.NEAREST:(e.minFilter==L.LINEAR_MIPMAP_LINEAR||e.minFilter==L.LINEAR_MIPMAP_NEAREST)&&(e.minFilter=L.LINEAR)),t||(e.wrapS=L.CLAMP_TO_EDGE,e.wrapT=L.CLAMP_TO_EDGE)}function Yl(e,t){return(e&e-1)===0&&(t&t-1)===0}const Kl=`@export clay.sm.depth.vertex
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
attribute vec3 position : POSITION;
attribute vec2 texcoord : TEXCOORD_0;
uniform vec2 uvRepeat = vec2(1.0, 1.0);
uniform vec2 uvOffset = vec2(0.0, 0.0);
@import clay.chunk.skinning_header
@import clay.chunk.instancing_header
varying vec4 v_ViewPosition;
varying vec2 v_Texcoord;
void main(){
 vec4 P = vec4(position, 1.0);
#ifdef SKINNING
 @import clay.chunk.skin_matrix
 P = skinMatrixWS * P;
#endif
#ifdef INSTANCING
 @import clay.chunk.instancing_matrix
 P = instanceMat * P;
#endif
 v_ViewPosition = worldViewProjection * P;
 gl_Position = v_ViewPosition;
 v_Texcoord = texcoord * uvRepeat + uvOffset;
}
@end
@export clay.sm.depth.fragment
varying vec4 v_ViewPosition;
varying vec2 v_Texcoord;
uniform float bias : 0.001;
uniform float slopeScale : 1.0;
uniform sampler2D alphaMap;
uniform float alphaCutoff: 0.0;
@import clay.util.encode_float
void main(){
 float depth = v_ViewPosition.z / v_ViewPosition.w;
 if (alphaCutoff > 0.0) {
 if (texture2D(alphaMap, v_Texcoord).a <= alphaCutoff) {
 discard;
 }
 }
#ifdef USE_VSM
 depth = depth * 0.5 + 0.5;
 float moment1 = depth;
 float moment2 = depth * depth;
 #ifdef SUPPORT_STANDARD_DERIVATIVES
 float dx = dFdx(depth);
 float dy = dFdy(depth);
 moment2 += 0.25*(dx*dx+dy*dy);
 #endif
 gl_FragColor = vec4(moment1, moment2, 0.0, 1.0);
#else
 #ifdef SUPPORT_STANDARD_DERIVATIVES
 float dx = dFdx(depth);
 float dy = dFdy(depth);
 depth += sqrt(dx*dx + dy*dy) * slopeScale + bias;
 #else
 depth += bias;
 #endif
 gl_FragColor = encodeFloat(depth * 0.5 + 0.5);
#endif
}
@end
@export clay.sm.debug_depth
uniform sampler2D depthMap;
varying vec2 v_Texcoord;
@import clay.util.decode_float
void main() {
 vec4 tex = texture2D(depthMap, v_Texcoord);
#ifdef USE_VSM
 gl_FragColor = vec4(tex.rgb, 1.0);
#else
 float depth = decodeFloat(tex);
 gl_FragColor = vec4(depth, depth, depth, 1.0);
#endif
}
@end
@export clay.sm.distance.vertex
uniform mat4 worldViewProjection : WORLDVIEWPROJECTION;
uniform mat4 world : WORLD;
attribute vec3 position : POSITION;
@import clay.chunk.skinning_header
varying vec3 v_WorldPosition;
void main (){
 vec4 P = vec4(position, 1.0);
#ifdef SKINNING
 @import clay.chunk.skin_matrix
 P = skinMatrixWS * P;
#endif
#ifdef INSTANCING
 @import clay.chunk.instancing_matrix
 P = instanceMat * P;
#endif
 gl_Position = worldViewProjection * P;
 v_WorldPosition = (world * P).xyz;
}
@end
@export clay.sm.distance.fragment
uniform vec3 lightPosition;
uniform float range : 100;
varying vec3 v_WorldPosition;
@import clay.util.encode_float
void main(){
 float dist = distance(lightPosition, v_WorldPosition);
#ifdef USE_VSM
 gl_FragColor = vec4(dist, dist * dist, 0.0, 0.0);
#else
 dist = dist / range;
 gl_FragColor = encodeFloat(dist);
#endif
}
@end
@export clay.plugin.shadow_map_common
@import clay.util.decode_float
float tapShadowMap(sampler2D map, vec2 uv, float z){
 vec4 tex = texture2D(map, uv);
 return step(z, decodeFloat(tex) * 2.0 - 1.0);
}
float pcf(sampler2D map, vec2 uv, float z, float textureSize, vec2 scale) {
 float shadowContrib = tapShadowMap(map, uv, z);
 vec2 offset = vec2(1.0 / textureSize) * scale;
#ifdef PCF_KERNEL_SIZE
 for (int _idx_ = 0; _idx_ < PCF_KERNEL_SIZE; _idx_++) {{
 shadowContrib += tapShadowMap(map, uv + offset * pcfKernel[_idx_], z);
 }}
 return shadowContrib / float(PCF_KERNEL_SIZE + 1);
#else
 shadowContrib += tapShadowMap(map, uv+vec2(offset.x, 0.0), z);
 shadowContrib += tapShadowMap(map, uv+vec2(offset.x, offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(-offset.x, offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(0.0, offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(-offset.x, 0.0), z);
 shadowContrib += tapShadowMap(map, uv+vec2(-offset.x, -offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(offset.x, -offset.y), z);
 shadowContrib += tapShadowMap(map, uv+vec2(0.0, -offset.y), z);
 return shadowContrib / 9.0;
#endif
}
float pcf(sampler2D map, vec2 uv, float z, float textureSize) {
 return pcf(map, uv, z, textureSize, vec2(1.0));
}
float chebyshevUpperBound(vec2 moments, float z){
 float p = 0.0;
 z = z * 0.5 + 0.5;
 if (z <= moments.x) {
 p = 1.0;
 }
 float variance = moments.y - moments.x * moments.x;
 variance = max(variance, 0.0000001);
 float mD = moments.x - z;
 float pMax = variance / (variance + mD * mD);
 pMax = clamp((pMax-0.4)/(1.0-0.4), 0.0, 1.0);
 return max(p, pMax);
}
float computeShadowContrib(
 sampler2D map, mat4 lightVPM, vec3 position, float textureSize, vec2 scale, vec2 offset
) {
 vec4 posInLightSpace = lightVPM * vec4(position, 1.0);
 posInLightSpace.xyz /= posInLightSpace.w;
 float z = posInLightSpace.z;
 if(all(greaterThan(posInLightSpace.xyz, vec3(-0.99, -0.99, -1.0))) &&
 all(lessThan(posInLightSpace.xyz, vec3(0.99, 0.99, 1.0)))){
 vec2 uv = (posInLightSpace.xy+1.0) / 2.0;
 #ifdef USE_VSM
 vec2 moments = texture2D(map, uv * scale + offset).xy;
 return chebyshevUpperBound(moments, z);
 #else
 return pcf(map, uv * scale + offset, z, textureSize, scale);
 #endif
 }
 return 1.0;
}
float computeShadowContrib(sampler2D map, mat4 lightVPM, vec3 position, float textureSize) {
 return computeShadowContrib(map, lightVPM, position, textureSize, vec2(1.0), vec2(0.0));
}
float computeShadowContribOmni(samplerCube map, vec3 direction, float range)
{
 float dist = length(direction);
 vec4 shadowTex = textureCube(map, direction);
#ifdef USE_VSM
 vec2 moments = shadowTex.xy;
 float variance = moments.y - moments.x * moments.x;
 float mD = moments.x - dist;
 float p = variance / (variance + mD * mD);
 if(moments.x + 0.001 < dist){
 return clamp(p, 0.0, 1.0);
 }else{
 return 1.0;
 }
#else
 return step(dist, (decodeFloat(shadowTex) + 0.0002) * range);
#endif
}
@end
@export clay.plugin.compute_shadow_map
#if defined(SPOT_LIGHT_SHADOWMAP_COUNT) || defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT) || defined(POINT_LIGHT_SHADOWMAP_COUNT)
#ifdef SPOT_LIGHT_SHADOWMAP_COUNT
uniform sampler2D spotLightShadowMaps[SPOT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform mat4 spotLightMatrices[SPOT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform float spotLightShadowMapSizes[SPOT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
#endif
#ifdef DIRECTIONAL_LIGHT_SHADOWMAP_COUNT
#if defined(SHADOW_CASCADE)
uniform sampler2D directionalLightShadowMaps[1]:unconfigurable;
uniform mat4 directionalLightMatrices[SHADOW_CASCADE]:unconfigurable;
uniform float directionalLightShadowMapSizes[1]:unconfigurable;
uniform float shadowCascadeClipsNear[SHADOW_CASCADE]:unconfigurable;
uniform float shadowCascadeClipsFar[SHADOW_CASCADE]:unconfigurable;
#else
uniform sampler2D directionalLightShadowMaps[DIRECTIONAL_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform mat4 directionalLightMatrices[DIRECTIONAL_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
uniform float directionalLightShadowMapSizes[DIRECTIONAL_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
#endif
#endif
#ifdef POINT_LIGHT_SHADOWMAP_COUNT
uniform samplerCube pointLightShadowMaps[POINT_LIGHT_SHADOWMAP_COUNT]:unconfigurable;
#endif
uniform bool shadowEnabled : true;
#ifdef PCF_KERNEL_SIZE
uniform vec2 pcfKernel[PCF_KERNEL_SIZE];
#endif
@import clay.plugin.shadow_map_common
#if defined(SPOT_LIGHT_SHADOWMAP_COUNT)
void computeShadowOfSpotLights(vec3 position, inout float shadowContribs[SPOT_LIGHT_COUNT] ) {
 float shadowContrib;
 for(int _idx_ = 0; _idx_ < SPOT_LIGHT_SHADOWMAP_COUNT; _idx_++) {{
 shadowContrib = computeShadowContrib(
 spotLightShadowMaps[_idx_], spotLightMatrices[_idx_], position,
 spotLightShadowMapSizes[_idx_]
 );
 shadowContribs[_idx_] = shadowContrib;
 }}
 for(int _idx_ = SPOT_LIGHT_SHADOWMAP_COUNT; _idx_ < SPOT_LIGHT_COUNT; _idx_++){{
 shadowContribs[_idx_] = 1.0;
 }}
}
#endif
#if defined(DIRECTIONAL_LIGHT_SHADOWMAP_COUNT)
#ifdef SHADOW_CASCADE
void computeShadowOfDirectionalLights(vec3 position, inout float shadowContribs[DIRECTIONAL_LIGHT_COUNT]){
 float depth = (2.0 * gl_FragCoord.z - gl_DepthRange.near - gl_DepthRange.far)
 / (gl_DepthRange.far - gl_DepthRange.near);
 float shadowContrib;
 shadowContribs[0] = 1.0;
 for (int _idx_ = 0; _idx_ < SHADOW_CASCADE; _idx_++) {{
 if (
 depth >= shadowCascadeClipsNear[_idx_] &&
 depth <= shadowCascadeClipsFar[_idx_]
 ) {
 shadowContrib = computeShadowContrib(
 directionalLightShadowMaps[0], directionalLightMatrices[_idx_], position,
 directionalLightShadowMapSizes[0],
 vec2(1.0 / float(SHADOW_CASCADE), 1.0),
 vec2(float(_idx_) / float(SHADOW_CASCADE), 0.0)
 );
 shadowContribs[0] = shadowContrib;
 }
 }}
 for(int _idx_ = DIRECTIONAL_LIGHT_SHADOWMAP_COUNT; _idx_ < DIRECTIONAL_LIGHT_COUNT; _idx_++) {{
 shadowContribs[_idx_] = 1.0;
 }}
}
#else
void computeShadowOfDirectionalLights(vec3 position, inout float shadowContribs[DIRECTIONAL_LIGHT_COUNT]){
 float shadowContrib;
 for(int _idx_ = 0; _idx_ < DIRECTIONAL_LIGHT_SHADOWMAP_COUNT; _idx_++) {{
 shadowContrib = computeShadowContrib(
 directionalLightShadowMaps[_idx_], directionalLightMatrices[_idx_], position,
 directionalLightShadowMapSizes[_idx_]
 );
 shadowContribs[_idx_] = shadowContrib;
 }}
 for(int _idx_ = DIRECTIONAL_LIGHT_SHADOWMAP_COUNT; _idx_ < DIRECTIONAL_LIGHT_COUNT; _idx_++) {{
 shadowContribs[_idx_] = 1.0;
 }}
}
#endif
#endif
#if defined(POINT_LIGHT_SHADOWMAP_COUNT)
void computeShadowOfPointLights(vec3 position, inout float shadowContribs[POINT_LIGHT_COUNT] ){
 vec3 lightPosition;
 vec3 direction;
 for(int _idx_ = 0; _idx_ < POINT_LIGHT_SHADOWMAP_COUNT; _idx_++) {{
 lightPosition = pointLightPosition[_idx_];
 direction = position - lightPosition;
 shadowContribs[_idx_] = computeShadowContribOmni(pointLightShadowMaps[_idx_], direction, pointLightRange[_idx_]);
 }}
 for(int _idx_ = POINT_LIGHT_SHADOWMAP_COUNT; _idx_ < POINT_LIGHT_COUNT; _idx_++) {{
 shadowContribs[_idx_] = 1.0;
 }}
}
#endif
#endif
@end`;var ht=["px","nx","py","ny","pz","nz"];z.import(Kl);function pi(e,t,r){if(r==="alphaMap")return e.material.get("diffuseMap");if(r==="alphaCutoff"){if(e.material.isDefined("fragment","ALPHA_TEST")&&e.material.get("diffuseMap")){var i=e.material.get("alphaCutoff");return i||0}return 0}else return r==="uvRepeat"?e.material.get("uvRepeat"):r==="uvOffset"?e.material.get("uvOffset"):t.get(r)}function Vn(e,t){var r=e.material,i=t.material;return r.get("diffuseMap")!==i.get("diffuseMap")||(r.get("alphaCutoff")||0)!==(i.get("alphaCutoff")||0)}var Ze=be.extend(function(){return{softShadow:Ze.PCF,shadowBlur:1,lightFrustumBias:"auto",kernelPCF:new Float32Array([1,0,1,1,-1,1,0,1,-1,0,-1,-1,1,-1,0,-1]),precision:"highp",_lastRenderNotCastShadow:!1,_frameBuffer:new me,_textures:{},_shadowMapNumber:{POINT_LIGHT:0,DIRECTIONAL_LIGHT:0,SPOT_LIGHT:0},_depthMaterials:{},_distanceMaterials:{},_receivers:[],_lightsCastShadow:[],_lightCameras:{},_lightMaterials:{},_texturePool:new Ur}},function(){this._gaussianPassH=new Me({fragment:z.source("clay.compositor.gaussian_blur")}),this._gaussianPassV=new Me({fragment:z.source("clay.compositor.gaussian_blur")}),this._gaussianPassH.setUniform("blurSize",this.shadowBlur),this._gaussianPassH.setUniform("blurDir",0),this._gaussianPassV.setUniform("blurSize",this.shadowBlur),this._gaussianPassV.setUniform("blurDir",1),this._outputDepthPass=new Me({fragment:z.source("clay.sm.debug_depth")})},{render:function(e,t,r,i){r||(r=t.getMainCamera()),this.trigger("beforerender",this,e,t,r),this._renderShadowPass(e,t,r,i),this.trigger("afterrender",this,e,t,r)},renderDebug:function(e,t){e.saveClear();var r=e.viewport,i=0,n=0,a=t||r.width/4,o=a;this.softShadow===Ze.VSM?this._outputDepthPass.material.define("fragment","USE_VSM"):this._outputDepthPass.material.undefine("fragment","USE_VSM");for(var s in this._textures){var l=this._textures[s];e.setViewport(i,n,a*l.width/l.height,o),this._outputDepthPass.setUniform("depthMap",l),this._outputDepthPass.render(e),i+=a*l.width/l.height}e.setViewport(r),e.restoreClear()},_updateReceivers:function(e,t){if(t.receiveShadow?(this._receivers.push(t),t.material.set("shadowEnabled",1),t.material.set("pcfKernel",this.kernelPCF)):t.material.set("shadowEnabled",0),this.softShadow===Ze.VSM)t.material.define("fragment","USE_VSM"),t.material.undefine("fragment","PCF_KERNEL_SIZE");else{t.material.undefine("fragment","USE_VSM");var r=this.kernelPCF;r&&r.length?t.material.define("fragment","PCF_KERNEL_SIZE",r.length/2):t.material.undefine("fragment","PCF_KERNEL_SIZE")}},_update:function(e,t){var r=this;t.traverse(function(a){a.isRenderable()&&r._updateReceivers(e,a)});for(var i=0;i<t.lights.length;i++){var n=t.lights[i];n.castShadow&&!n.invisible&&this._lightsCastShadow.push(n)}},_renderShadowPass:function(e,t,r,i){for(var n in this._shadowMapNumber)this._shadowMapNumber[n]=0;this._lightsCastShadow.length=0,this._receivers.length=0;var a=e.gl;if(i||t.update(),r&&r.update(),t.updateLights(),this._update(e,t),!this._lightsCastShadow.length&&this._lastRenderNotCastShadow)return;this._lastRenderNotCastShadow=this._lightsCastShadow===0,a.enable(a.DEPTH_TEST),a.depthMask(!0),a.disable(a.BLEND),a.clearColor(1,1,1,1);for(var o=[],s=[],l=[],u=[],f=[],h=[],d,c=0;c<this._lightsCastShadow.length;c++){var v=this._lightsCastShadow[c];if(v.type==="DIRECTIONAL_LIGHT"){if(d){console.warn("Only one direectional light supported with shadow cascade");continue}if(v.shadowCascade>4){console.warn("Support at most 4 cascade");continue}v.shadowCascade>1&&(d=v),this.renderDirectionalLightShadow(e,t,r,v,f,u,l)}else v.type==="SPOT_LIGHT"?this.renderSpotLightShadow(e,t,v,s,o):v.type==="POINT_LIGHT"&&this.renderPointLightShadow(e,t,v,h);this._shadowMapNumber[v.type]++}for(var p in this._shadowMapNumber)for(var m=this._shadowMapNumber[p],_=p+"_SHADOWMAP_COUNT",c=0;c<this._receivers.length;c++){var x=this._receivers[c],T=x.material;T.fragmentDefines[_]!==m&&(m>0?T.define("fragment",_,m):T.isDefined("fragment",_)&&T.undefine("fragment",_))}for(var c=0;c<this._receivers.length;c++){var x=this._receivers[c],T=x.material;d?T.define("fragment","SHADOW_CASCADE",d.shadowCascade):T.undefine("fragment","SHADOW_CASCADE")}var g=t.shadowUniforms;function E(H){return H.height}if(l.length>0){var S=l.map(E);if(g.directionalLightShadowMaps={value:l,type:"tv"},g.directionalLightMatrices={value:u,type:"m4v"},g.directionalLightShadowMapSizes={value:S,type:"1fv"},d){var C=f.slice(),A=f.slice();C.pop(),A.shift(),C.reverse(),A.reverse(),u.reverse(),g.shadowCascadeClipsNear={value:C,type:"1fv"},g.shadowCascadeClipsFar={value:A,type:"1fv"}}}if(o.length>0){var N=o.map(E),g=t.shadowUniforms;g.spotLightShadowMaps={value:o,type:"tv"},g.spotLightMatrices={value:s,type:"m4v"},g.spotLightShadowMapSizes={value:N,type:"1fv"}}h.length>0&&(g.pointLightShadowMaps={value:h,type:"tv"})},renderDirectionalLightShadow:(function(){var e=new Hr,t=new F,r=new Ee,i=new F,n=new F,a=new F,o=new F;return function(s,l,u,f,h,d,c){var v=this._getDepthMaterial(f),p={getMaterial:function(de){return de.shadowDepthMaterial||v},isMaterialChanged:Vn,getUniform:pi,ifRender:function(de){return de.castShadow},sortCompare:Ve.opaqueSortCompare};if(!l.viewBoundingBoxLastFrame.isFinite()){var m=l.getBoundingBox();l.viewBoundingBoxLastFrame.copy(m).applyTransform(u.viewMatrix)}var _=Math.min(-l.viewBoundingBoxLastFrame.min.z,u.far),x=Math.max(-l.viewBoundingBoxLastFrame.max.z,u.near),T=this._getDirectionalLightCamera(f,l,u),g=a.array;o.copy(T.projectionMatrix),D.invert(n.array,T.worldTransform.array),D.multiply(n.array,n.array,u.worldTransform.array),D.multiply(g,o.array,n.array);for(var E=[],S=u instanceof ge,C=(u.near+u.far)/(u.near-u.far),A=2*u.near*u.far/(u.near-u.far),N=0;N<=f.shadowCascade;N++){var H=x*Math.pow(_/x,N/f.shadowCascade),R=x+(_-x)*N/f.shadowCascade,U=H*f.cascadeSplitLogFactor+R*(1-f.cascadeSplitLogFactor);E.push(U),h.push(-(-U*C+A)/-U)}var V=this._getTexture(f,f.shadowCascade);c.push(V);var I=s.viewport,G=s.gl;this._frameBuffer.attach(V),this._frameBuffer.bind(s),G.clear(G.COLOR_BUFFER_BIT|G.DEPTH_BUFFER_BIT);for(var N=0;N<f.shadowCascade;N++){var X=E[N],q=E[N+1];S?D.perspective(t.array,u.fov/180*Math.PI,u.aspect,X,q):D.ortho(t.array,u.left,u.right,u.bottom,u.top,X,q),e.setFromProjection(t),e.getTransformedBoundingBox(r,n),r.applyProjection(o);var ie=r.min.array,_e=r.max.array;ie[0]=Math.max(ie[0],-1),ie[1]=Math.max(ie[1],-1),_e[0]=Math.min(_e[0],1),_e[1]=Math.min(_e[1],1),i.ortho(ie[0],_e[0],ie[1],_e[1],1,-1),T.projectionMatrix.multiplyLeft(i);var we=f.shadowResolution||512;s.setViewport((f.shadowCascade-N-1)*we,0,we,we,1);var ce=l.updateRenderList(T);s.renderPass(ce.opaque,T,p),this.softShadow===Ze.VSM&&this._gaussianFilter(s,V,V.width);var xe=new F;xe.copy(T.viewMatrix).multiplyLeft(T.projectionMatrix),d.push(xe.array),T.projectionMatrix.copy(o)}this._frameBuffer.unbind(s),s.setViewport(I)}})(),renderSpotLightShadow:function(e,t,r,i,n){var a=this._getTexture(r),o=this._getSpotLightCamera(r),s=e.gl;this._frameBuffer.attach(a),this._frameBuffer.bind(e),s.clear(s.COLOR_BUFFER_BIT|s.DEPTH_BUFFER_BIT);var l=this._getDepthMaterial(r),u={getMaterial:function(d){return d.shadowDepthMaterial||l},isMaterialChanged:Vn,getUniform:pi,ifRender:function(d){return d.castShadow},sortCompare:Ve.opaqueSortCompare},f=t.updateRenderList(o);e.renderPass(f.opaque,o,u),this._frameBuffer.unbind(e),this.softShadow===Ze.VSM&&this._gaussianFilter(e,a,a.width);var h=new F;h.copy(o.worldTransform).invert().multiplyLeft(o.projectionMatrix),n.push(a),i.push(h.array)},renderPointLightShadow:function(e,t,r,i){var n=this._getTexture(r),a=e.gl;i.push(n);var o=this._getDepthMaterial(r),s={getMaterial:function(x){return x.shadowDepthMaterial||o},getUniform:pi,sortCompare:Ve.opaqueSortCompare},l={px:[],py:[],pz:[],nx:[],ny:[],nz:[]},u=new Ee,f=r.getWorldPosition().array,h=new Ee,d=r.range;h.min.setArray(f),h.max.setArray(f);var c=new b(d,d,d);h.max.add(c),h.min.sub(c);var v={px:!1,py:!1,pz:!1,nx:!1,ny:!1,nz:!1};t.traverse(function(x){if(x.isRenderable()&&x.castShadow){var T=x.geometry;if(!T.boundingBox){for(var g=0;g<ht.length;g++)l[ht[g]].push(x);return}if(u.transformFrom(T.boundingBox,x.worldTransform),!u.intersectBoundingBox(h))return;u.updateVertices();for(var g=0;g<ht.length;g++)v[ht[g]]=!1;for(var g=0;g<8;g++){var E=u.vertices[g],S=E[0]-f[0],C=E[1]-f[1],A=E[2]-f[2],N=Math.abs(S),H=Math.abs(C),R=Math.abs(A);N>H?N>R?v[S>0?"px":"nx"]=!0:v[A>0?"pz":"nz"]=!0:H>R?v[C>0?"py":"ny"]=!0:v[A>0?"pz":"nz"]=!0}for(var g=0;g<ht.length;g++)v[ht[g]]&&l[ht[g]].push(x)}});for(var p=0;p<6;p++){var m=ht[p],_=this._getPointLightCamera(r,m);this._frameBuffer.attach(n,a.COLOR_ATTACHMENT0,a.TEXTURE_CUBE_MAP_POSITIVE_X+p),this._frameBuffer.bind(e),a.clear(a.COLOR_BUFFER_BIT|a.DEPTH_BUFFER_BIT),e.renderPass(l[m],_,s)}this._frameBuffer.unbind(e)},_getDepthMaterial:function(e){var t=this._lightMaterials[e.__uid__],r=e.type==="POINT_LIGHT";if(!t){var i=r?"clay.sm.distance.":"clay.sm.depth.";t=new at({precision:this.precision,shader:new z(z.source(i+"vertex"),z.source(i+"fragment"))}),this._lightMaterials[e.__uid__]=t}return e.shadowSlopeScale!=null&&t.setUniform("slopeScale",e.shadowSlopeScale),e.shadowBias!=null&&t.setUniform("bias",e.shadowBias),this.softShadow===Ze.VSM?t.define("fragment","USE_VSM"):t.undefine("fragment","USE_VSM"),r&&(t.set("lightPosition",e.getWorldPosition().array),t.set("range",e.range)),t},_gaussianFilter:function(e,t,r){var i={width:r,height:r,type:O.FLOAT},n=this._texturePool.get(i);this._frameBuffer.attach(n),this._frameBuffer.bind(e),this._gaussianPassH.setUniform("texture",t),this._gaussianPassH.setUniform("textureWidth",r),this._gaussianPassH.render(e),this._frameBuffer.attach(t),this._gaussianPassV.setUniform("texture",n),this._gaussianPassV.setUniform("textureHeight",r),this._gaussianPassV.render(e),this._frameBuffer.unbind(e),this._texturePool.put(n)},_getTexture:function(e,t){var r=e.__uid__,i=this._textures[r],n=e.shadowResolution||512;return t=t||1,i||(e.type==="POINT_LIGHT"?i=new At:i=new K,i.width=n*t,i.height=n,this.softShadow===Ze.VSM?(i.type=O.FLOAT,i.anisotropic=4):(i.minFilter=L.NEAREST,i.magFilter=L.NEAREST,i.useMipmap=!1),this._textures[r]=i),i},_getPointLightCamera:function(e,t){this._lightCameras.point||(this._lightCameras.point={px:new ge,nx:new ge,py:new ge,ny:new ge,pz:new ge,nz:new ge});var r=this._lightCameras.point[t];switch(r.far=e.range,r.fov=90,r.position.set(0,0,0),t){case"px":r.lookAt(b.POSITIVE_X,b.NEGATIVE_Y);break;case"nx":r.lookAt(b.NEGATIVE_X,b.NEGATIVE_Y);break;case"py":r.lookAt(b.POSITIVE_Y,b.POSITIVE_Z);break;case"ny":r.lookAt(b.NEGATIVE_Y,b.NEGATIVE_Z);break;case"pz":r.lookAt(b.POSITIVE_Z,b.NEGATIVE_Y);break;case"nz":r.lookAt(b.NEGATIVE_Z,b.NEGATIVE_Y);break}return e.getWorldPosition(r.position),r.update(),r},_getDirectionalLightCamera:(function(){var e=new F,t=new Ee,r=new Ee;return function(i,n,a){this._lightCameras.directional||(this._lightCameras.directional=new ur);var o=this._lightCameras.directional;t.copy(n.viewBoundingBoxLastFrame),t.intersection(a.frustum.boundingBox),o.position.copy(t.min).add(t.max).scale(.5).transformMat4(a.worldTransform),o.rotation.copy(i.rotation),o.scale.copy(i.scale),o.updateWorldTransform(),F.invert(e,o.worldTransform),F.multiply(e,e,a.worldTransform),r.copy(t).applyTransform(e);var s=r.min.array,l=r.max.array;return o.position.set((s[0]+l[0])/2,(s[1]+l[1])/2,l[2]).transformMat4(o.worldTransform),o.near=0,o.far=-s[2]+l[2],isNaN(this.lightFrustumBias)?o.far*=4:o.far+=this.lightFrustumBias,o.left=s[0],o.right=l[0],o.top=l[1],o.bottom=s[1],o.update(!0),o}})(),_getSpotLightCamera:function(e){this._lightCameras.spot||(this._lightCameras.spot=new ge);var t=this._lightCameras.spot;return t.fov=e.penumbraAngle*2,t.far=e.range,t.worldTransform.copy(e.worldTransform),t.updateProjectionMatrix(),D.invert(t.viewMatrix.array,t.worldTransform.array),t},dispose:function(e){var t=e.gl||e;this._frameBuffer&&this._frameBuffer.dispose(t);for(var r in this._textures)this._textures[r].dispose(t);this._texturePool.clear(e.gl),this._depthMaterials={},this._distanceMaterials={},this._textures={},this._lightCameras={},this._shadowMapNumber={POINT_LIGHT:0,DIRECTIONAL_LIGHT:0,SPOT_LIGHT:0},this._meshMaterials={};for(var i=0;i<this._receivers.length;i++){var n=this._receivers[i];if(n.material){var a=n.material;a.undefine("fragment","POINT_LIGHT_SHADOW_COUNT"),a.undefine("fragment","DIRECTIONAL_LIGHT_SHADOW_COUNT"),a.undefine("fragment","AMBIENT_LIGHT_SHADOW_COUNT"),a.set("shadowEnabled",0)}}this._receivers=[],this._lightsCastShadow=[]}});Ze.VSM=1;Ze.PCF=2;var fr=be.extend(function(){return{name:"",inputLinks:{},outputLinks:{},_prevOutputTextures:{},_outputTextures:{},_outputReferences:{},_rendering:!1,_rendered:!1,_compositor:null}},{updateParameter:function(e,t){var r=this.outputs[e],i=r.parameters,n=r._parametersCopy;if(n||(n=r._parametersCopy={}),i)for(var a in i)a!=="width"&&a!=="height"&&(n[a]=i[a]);var o,s;return i.width instanceof Function?o=i.width.call(this,t):o=i.width,i.height instanceof Function?s=i.height.call(this,t):s=i.height,(n.width!==o||n.height!==s)&&this._outputTextures[e]&&this._outputTextures[e].dispose(t.gl),n.width=o,n.height=s,n},setParameter:function(e,t){},getParameter:function(e){},setParameters:function(e){for(var t in e)this.setParameter(t,e[t])},render:function(){},getOutput:function(e,t){if(t==null)return t=e,this._outputTextures[t];var r=this.outputs[t];if(r)return this._rendered?r.outputLastFrame?this._prevOutputTextures[t]:this._outputTextures[t]:this._rendering?(this._prevOutputTextures[t]||(this._prevOutputTextures[t]=this._compositor.allocateTexture(r.parameters||{})),this._prevOutputTextures[t]):(this.render(e),this._outputTextures[t])},removeReference:function(e){if(this._outputReferences[e]--,this._outputReferences[e]===0){var t=this.outputs[e];t.keepLastFrame?(this._prevOutputTextures[e]&&this._compositor.releaseTexture(this._prevOutputTextures[e]),this._prevOutputTextures[e]=this._outputTextures[e]):this._compositor.releaseTexture(this._outputTextures[e])}},link:function(e,t,r){this.inputLinks[e]={node:t,pin:r},t.outputLinks[r]||(t.outputLinks[r]=[]),t.outputLinks[r].push({node:this,pin:e}),this.pass.material.enableTexture(e)},clear:function(){this.inputLinks={},this.outputLinks={}},updateReference:function(e){if(!this._rendering){this._rendering=!0;for(var t in this.inputLinks){var r=this.inputLinks[t];r.node.updateReference(r.pin)}this._rendering=!1}e&&this._outputReferences[e]++},beforeFrame:function(){this._rendered=!1;for(var e in this.outputLinks)this._outputReferences[e]=0},afterFrame:function(){for(var e in this.outputLinks)if(this._outputReferences[e]>0){var t=this.outputs[e];t.keepLastFrame?(this._prevOutputTextures[e]&&this._compositor.releaseTexture(this._prevOutputTextures[e]),this._prevOutputTextures[e]=this._outputTextures[e]):this._compositor.releaseTexture(this._outputTextures[e])}}}),Gn=be.extend(function(){return{nodes:[]}},{dirty:function(){this._dirty=!0},addNode:function(e){this.nodes.indexOf(e)>=0||(this.nodes.push(e),this._dirty=!0)},removeNode:function(e){typeof e=="string"&&(e=this.getNodeByName(e));var t=this.nodes.indexOf(e);t>=0&&(this.nodes.splice(t,1),this._dirty=!0)},getNodeByName:function(e){for(var t=0;t<this.nodes.length;t++)if(this.nodes[t].name===e)return this.nodes[t]},update:function(){for(var e=0;e<this.nodes.length;e++)this.nodes[e].clear();for(var e=0;e<this.nodes.length;e++){var t=this.nodes[e];if(t.inputs){for(var r in t.inputs)if(t.inputs[r]){if(t.pass&&!t.pass.material.isUniformEnabled(r)){console.warn("Pin "+t.name+"."+r+" not used.");continue}var i=t.inputs[r],n=this.findPin(i);n?t.link(r,n.node,n.pin):console.warn(typeof i=="string"?"Node "+i+" not exist":"Pin of "+i.node+"."+i.pin+" not exist")}}}},findPin:function(e){var t;if((typeof e=="string"||e instanceof fr)&&(e={node:e}),typeof e.node=="string")for(var r=0;r<this.nodes.length;r++){var i=this.nodes[r];i.name===e.node&&(t=i)}else t=e.node;if(t){var n=e.pin;if(n||t.outputs&&(n=Object.keys(t.outputs)[0]),t.outputs[n])return{node:t,pin:n}}}}),Ql=Gn.extend(function(){return{_outputs:[],_texturePool:new Ur,_frameBuffer:new me({depthBuffer:!1})}},{addNode:function(e){Gn.prototype.addNode.call(this,e),e._compositor=this},render:function(e,t){if(this._dirty){this.update(),this._dirty=!1,this._outputs.length=0;for(var r=0;r<this.nodes.length;r++)this.nodes[r].outputs||this._outputs.push(this.nodes[r])}for(var r=0;r<this.nodes.length;r++)this.nodes[r].beforeFrame();for(var r=0;r<this._outputs.length;r++)this._outputs[r].updateReference();for(var r=0;r<this._outputs.length;r++)this._outputs[r].render(e,t);for(var r=0;r<this.nodes.length;r++)this.nodes[r].afterFrame()},allocateTexture:function(e){return this._texturePool.get(e)},releaseTexture:function(e){this._texturePool.put(e)},getFrameBuffer:function(){return this._frameBuffer},dispose:function(e){this._texturePool.clear(e)}}),Jl=fr.extend({name:"scene",scene:null,camera:null,autoUpdateScene:!0,preZ:!1},function(){this.frameBuffer=new me},{render:function(e){this._rendering=!0;var t=e.gl;this.trigger("beforerender");var r;if(!this.outputs)r=e.render(this.scene,this.camera,!this.autoUpdateScene,this.preZ);else{var i=this.frameBuffer;for(var n in this.outputs){var a=this.updateParameter(n,e),o=this.outputs[n],s=this._compositor.allocateTexture(a);this._outputTextures[n]=s;var l=o.attachment||t.COLOR_ATTACHMENT0;typeof l=="string"&&(l=t[l]),i.attach(s,l)}i.bind(e);var u=e.getGLExtension("EXT_draw_buffers");if(u){var f=[];for(var l in this.outputs)l=parseInt(l),l>=t.COLOR_ATTACHMENT0&&l<=t.COLOR_ATTACHMENT0+8&&f.push(l);u.drawBuffersEXT(f)}e.saveClear(),e.clearBit=L.DEPTH_BUFFER_BIT|L.COLOR_BUFFER_BIT,r=e.render(this.scene,this.camera,!this.autoUpdateScene,this.preZ),e.restoreClear(),i.unbind(e)}this.trigger("afterrender",r),this._rendering=!1,this._rendered=!0}}),$l=fr.extend(function(){return{texture:null,outputs:{color:{}}}},function(){},{getOutput:function(e,t){return this.texture},beforeFrame:function(){},afterFrame:function(){}}),eu=fr.extend(function(){return{name:"",inputs:{},outputs:null,shader:"",inputLinks:{},outputLinks:{},pass:null,_prevOutputTextures:{},_outputTextures:{},_outputReferences:{},_rendering:!1,_rendered:!1,_compositor:null}},function(){var e=new Me({fragment:this.shader});this.pass=e},{render:function(e,t){this.trigger("beforerender",e),this._rendering=!0;var r=e.gl;for(var i in this.inputLinks){var n=this.inputLinks[i],a=n.node.getOutput(e,n.pin);this.pass.setUniform(i,a)}if(!this.outputs)this.pass.outputs=null,this._compositor.getFrameBuffer().unbind(e),this.pass.render(e,t);else{this.pass.outputs={};var o={};for(var s in this.outputs){var l=this.updateParameter(s,e);isNaN(l.width)&&this.updateParameter(s,e);var u=this.outputs[s],f=this._compositor.allocateTexture(l);this._outputTextures[s]=f;var h=u.attachment||r.COLOR_ATTACHMENT0;typeof h=="string"&&(h=r[h]),o[h]=f}this._compositor.getFrameBuffer().bind(e);for(var h in o)this._compositor.getFrameBuffer().attach(o[h],h);this.pass.render(e),this._compositor.getFrameBuffer().updateMipmap(e)}for(var i in this.inputLinks){var n=this.inputLinks[i];n.node.removeReference(n.pin)}this._rendering=!1,this._rendered=!0,this.trigger("afterrender",e)},updateParameter:function(e,t){var r=this.outputs[e],i=r.parameters,n=r._parametersCopy;if(n||(n=r._parametersCopy={}),i)for(var a in i)a!=="width"&&a!=="height"&&(n[a]=i[a]);var o,s;return typeof i.width=="function"?o=i.width.call(this,t):o=i.width,typeof i.height=="function"?s=i.height.call(this,t):s=i.height,o=Math.ceil(o),s=Math.ceil(s),(n.width!==o||n.height!==s)&&this._outputTextures[e]&&this._outputTextures[e].dispose(t),n.width=o,n.height=s,n},setParameter:function(e,t){this.pass.setUniform(e,t)},getParameter:function(e){return this.pass.getUniform(e)},setParameters:function(e){for(var t in e)this.setParameter(t,e[t])},define:function(e,t){this.pass.material.define("fragment",e,t)},undefine:function(e){this.pass.material.undefine("fragment",e)},removeReference:function(e){if(this._outputReferences[e]--,this._outputReferences[e]===0){var t=this.outputs[e];t.keepLastFrame?(this._prevOutputTextures[e]&&this._compositor.releaseTexture(this._prevOutputTextures[e]),this._prevOutputTextures[e]=this._outputTextures[e]):this._compositor.releaseTexture(this._outputTextures[e])}},clear:function(){fr.prototype.clear.call(this),this.pass.material.disableTexturesAll()}});const tu=`@export clay.compositor.coloradjust
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float brightness : 0.0;
uniform float contrast : 1.0;
uniform float exposure : 0.0;
uniform float gamma : 1.0;
uniform float saturation : 1.0;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord);
 vec3 color = clamp(tex.rgb + vec3(brightness), 0.0, 1.0);
 color = clamp( (color-vec3(0.5))*contrast+vec3(0.5), 0.0, 1.0);
 color = clamp( color * pow(2.0, exposure), 0.0, 1.0);
 color = clamp( pow(color, vec3(gamma)), 0.0, 1.0);
 float luminance = dot( color, w );
 color = mix(vec3(luminance), color, saturation);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.brightness
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float brightness : 0.0;
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord);
 vec3 color = tex.rgb + vec3(brightness);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.contrast
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float contrast : 1.0;
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord);
 vec3 color = (tex.rgb-vec3(0.5))*contrast+vec3(0.5);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.exposure
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float exposure : 0.0;
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 vec3 color = tex.rgb * pow(2.0, exposure);
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.gamma
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float gamma : 1.0;
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 vec3 color = pow(tex.rgb, vec3(gamma));
 gl_FragColor = vec4(color, tex.a);
}
@end
@export clay.compositor.saturation
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float saturation : 1.0;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 vec3 color = tex.rgb;
 float luminance = dot(color, w);
 color = mix(vec3(luminance), color, saturation);
 gl_FragColor = vec4(color, tex.a);
}
@end`,Da=`@export clay.compositor.kernel.gaussian_9
float gaussianKernel[9];
gaussianKernel[0] = 0.07;
gaussianKernel[1] = 0.09;
gaussianKernel[2] = 0.12;
gaussianKernel[3] = 0.14;
gaussianKernel[4] = 0.16;
gaussianKernel[5] = 0.14;
gaussianKernel[6] = 0.12;
gaussianKernel[7] = 0.09;
gaussianKernel[8] = 0.07;
@end
@export clay.compositor.kernel.gaussian_13
float gaussianKernel[13];
gaussianKernel[0] = 0.02;
gaussianKernel[1] = 0.03;
gaussianKernel[2] = 0.06;
gaussianKernel[3] = 0.08;
gaussianKernel[4] = 0.11;
gaussianKernel[5] = 0.13;
gaussianKernel[6] = 0.14;
gaussianKernel[7] = 0.13;
gaussianKernel[8] = 0.11;
gaussianKernel[9] = 0.08;
gaussianKernel[10] = 0.06;
gaussianKernel[11] = 0.03;
gaussianKernel[12] = 0.02;
@end
@export clay.compositor.gaussian_blur
#define SHADER_NAME gaussian_blur
uniform sampler2D texture;varying vec2 v_Texcoord;
uniform float blurSize : 2.0;
uniform vec2 textureSize : [512.0, 512.0];
uniform float blurDir : 0.0;
@import clay.util.rgbm
@import clay.util.clamp_sample
void main (void)
{
 @import clay.compositor.kernel.gaussian_9
 vec2 off = blurSize / textureSize;
 off *= vec2(1.0 - blurDir, blurDir);
 vec4 sum = vec4(0.0);
 float weightAll = 0.0;
 for (int i = 0; i < 9; i++) {
 float w = gaussianKernel[i];
 vec4 texel = decodeHDR(clampSample(texture, v_Texcoord + float(i - 4) * off));
 sum += texel * w;
 weightAll += w;
 }
 gl_FragColor = encodeHDR(sum / max(weightAll, 0.01));
}
@end
`,ru=`@export clay.compositor.hdr.log_lum
varying vec2 v_Texcoord;
uniform sampler2D texture;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
@import clay.util.rgbm
void main()
{
 vec4 tex = decodeHDR(texture2D(texture, v_Texcoord));
 float luminance = dot(tex.rgb, w);
 luminance = log(luminance + 0.001);
 gl_FragColor = encodeHDR(vec4(vec3(luminance), 1.0));
}
@end
@export clay.compositor.hdr.lum_adaption
varying vec2 v_Texcoord;
uniform sampler2D adaptedLum;
uniform sampler2D currentLum;
uniform float frameTime : 0.02;
@import clay.util.rgbm
void main()
{
 float fAdaptedLum = decodeHDR(texture2D(adaptedLum, vec2(0.5, 0.5))).r;
 float fCurrentLum = exp(encodeHDR(texture2D(currentLum, vec2(0.5, 0.5))).r);
 fAdaptedLum += (fCurrentLum - fAdaptedLum) * (1.0 - pow(0.98, 30.0 * frameTime));
 gl_FragColor = encodeHDR(vec4(vec3(fAdaptedLum), 1.0));
}
@end
@export clay.compositor.lum
varying vec2 v_Texcoord;
uniform sampler2D texture;
const vec3 w = vec3(0.2125, 0.7154, 0.0721);
void main()
{
 vec4 tex = texture2D( texture, v_Texcoord );
 float luminance = dot(tex.rgb, w);
 gl_FragColor = vec4(vec3(luminance), 1.0);
}
@end`,Pa=`
@export clay.compositor.lut
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform sampler2D lookup;
void main()
{
 vec4 tex = texture2D(texture, v_Texcoord);
 float blueColor = tex.b * 63.0;
 vec2 quad1;
 quad1.y = floor(floor(blueColor) / 8.0);
 quad1.x = floor(blueColor) - (quad1.y * 8.0);
 vec2 quad2;
 quad2.y = floor(ceil(blueColor) / 8.0);
 quad2.x = ceil(blueColor) - (quad2.y * 8.0);
 vec2 texPos1;
 texPos1.x = (quad1.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.r);
 texPos1.y = (quad1.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.g);
 vec2 texPos2;
 texPos2.x = (quad2.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.r);
 texPos2.y = (quad2.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * tex.g);
 vec4 newColor1 = texture2D(lookup, texPos1);
 vec4 newColor2 = texture2D(lookup, texPos2);
 vec4 newColor = mix(newColor1, newColor2, fract(blueColor));
 gl_FragColor = vec4(newColor.rgb, tex.w);
}
@end`,iu=`@export clay.compositor.vignette
#define OUTPUT_ALPHA
varying vec2 v_Texcoord;
uniform sampler2D texture;
uniform float darkness: 1;
uniform float offset: 1;
@import clay.util.rgbm
void main()
{
 vec4 texel = decodeHDR(texture2D(texture, v_Texcoord));
 gl_FragColor.rgb = texel.rgb;
 vec2 uv = (v_Texcoord - vec2(0.5)) * vec2(offset);
 gl_FragColor = encodeHDR(vec4(mix(texel.rgb, vec3(1.0 - darkness), dot(uv, uv)), texel.a));
}
@end`,Na=`@export clay.compositor.output
#define OUTPUT_ALPHA
varying vec2 v_Texcoord;
uniform sampler2D texture;
@import clay.util.rgbm
void main()
{
 vec4 tex = decodeHDR(texture2D(texture, v_Texcoord));
 gl_FragColor.rgb = tex.rgb;
#ifdef OUTPUT_ALPHA
 gl_FragColor.a = tex.a;
#else
 gl_FragColor.a = 1.0;
#endif
 gl_FragColor = encodeHDR(gl_FragColor);
#ifdef PREMULTIPLY_ALPHA
 gl_FragColor.rgb *= gl_FragColor.a;
#endif
}
@end`,Ra=`@export clay.compositor.bright
uniform sampler2D texture;
uniform float threshold : 1;
uniform float scale : 1.0;
uniform vec2 textureSize: [512, 512];
varying vec2 v_Texcoord;
const vec3 lumWeight = vec3(0.2125, 0.7154, 0.0721);
@import clay.util.rgbm
vec4 median(vec4 a, vec4 b, vec4 c)
{
 return a + b + c - min(min(a, b), c) - max(max(a, b), c);
}
void main()
{
 vec4 texel = decodeHDR(texture2D(texture, v_Texcoord));
#ifdef ANTI_FLICKER
 vec3 d = 1.0 / textureSize.xyx * vec3(1.0, 1.0, 0.0);
 vec4 s1 = decodeHDR(texture2D(texture, v_Texcoord - d.xz));
 vec4 s2 = decodeHDR(texture2D(texture, v_Texcoord + d.xz));
 vec4 s3 = decodeHDR(texture2D(texture, v_Texcoord - d.zy));
 vec4 s4 = decodeHDR(texture2D(texture, v_Texcoord + d.zy));
 texel = median(median(texel, s1, s2), s3, s4);
#endif
 float lum = dot(texel.rgb , lumWeight);
 vec4 color;
 if (lum > threshold && texel.a > 0.0)
 {
 color = vec4(texel.rgb * scale, texel.a * scale);
 }
 else
 {
 color = vec4(0.0);
 }
 gl_FragColor = encodeHDR(color);
}
@end
`,Oa=`@export clay.compositor.downsample
uniform sampler2D texture;
uniform vec2 textureSize : [512, 512];
varying vec2 v_Texcoord;
@import clay.util.rgbm
float brightness(vec3 c)
{
 return max(max(c.r, c.g), c.b);
}
@import clay.util.clamp_sample
void main()
{
 vec4 d = vec4(-1.0, -1.0, 1.0, 1.0) / textureSize.xyxy;
#ifdef ANTI_FLICKER
 vec3 s1 = decodeHDR(clampSample(texture, v_Texcoord + d.xy)).rgb;
 vec3 s2 = decodeHDR(clampSample(texture, v_Texcoord + d.zy)).rgb;
 vec3 s3 = decodeHDR(clampSample(texture, v_Texcoord + d.xw)).rgb;
 vec3 s4 = decodeHDR(clampSample(texture, v_Texcoord + d.zw)).rgb;
 float s1w = 1.0 / (brightness(s1) + 1.0);
 float s2w = 1.0 / (brightness(s2) + 1.0);
 float s3w = 1.0 / (brightness(s3) + 1.0);
 float s4w = 1.0 / (brightness(s4) + 1.0);
 float oneDivideSum = 1.0 / (s1w + s2w + s3w + s4w);
 vec4 color = vec4(
 (s1 * s1w + s2 * s2w + s3 * s3w + s4 * s4w) * oneDivideSum,
 1.0
 );
#else
 vec4 color = decodeHDR(clampSample(texture, v_Texcoord + d.xy));
 color += decodeHDR(clampSample(texture, v_Texcoord + d.zy));
 color += decodeHDR(clampSample(texture, v_Texcoord + d.xw));
 color += decodeHDR(clampSample(texture, v_Texcoord + d.zw));
 color *= 0.25;
#endif
 gl_FragColor = encodeHDR(color);
}
@end`,Ia=`
@export clay.compositor.upsample
#define HIGH_QUALITY
uniform sampler2D texture;
uniform vec2 textureSize : [512, 512];
uniform float sampleScale: 0.5;
varying vec2 v_Texcoord;
@import clay.util.rgbm
@import clay.util.clamp_sample
void main()
{
#ifdef HIGH_QUALITY
 vec4 d = vec4(1.0, 1.0, -1.0, 0.0) / textureSize.xyxy * sampleScale;
 vec4 s;
 s = decodeHDR(clampSample(texture, v_Texcoord - d.xy));
 s += decodeHDR(clampSample(texture, v_Texcoord - d.wy)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord - d.zy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zw)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord )) * 4.0;
 s += decodeHDR(clampSample(texture, v_Texcoord + d.xw)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.wy)) * 2.0;
 s += decodeHDR(clampSample(texture, v_Texcoord + d.xy));
 gl_FragColor = encodeHDR(s / 16.0);
#else
 vec4 d = vec4(-1.0, -1.0, +1.0, +1.0) / textureSize.xyxy;
 vec4 s;
 s = decodeHDR(clampSample(texture, v_Texcoord + d.xy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zy));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.xw));
 s += decodeHDR(clampSample(texture, v_Texcoord + d.zw));
 gl_FragColor = encodeHDR(s / 4.0);
#endif
}
@end`,Ba=`@export clay.compositor.hdr.composite
#define TONEMAPPING
uniform sampler2D texture;
#ifdef BLOOM_ENABLED
uniform sampler2D bloom;
#endif
#ifdef LENSFLARE_ENABLED
uniform sampler2D lensflare;
uniform sampler2D lensdirt;
#endif
#ifdef LUM_ENABLED
uniform sampler2D lum;
#endif
#ifdef LUT_ENABLED
uniform sampler2D lut;
#endif
#ifdef COLOR_CORRECTION
uniform float brightness : 0.0;
uniform float contrast : 1.0;
uniform float saturation : 1.0;
#endif
#ifdef VIGNETTE
uniform float vignetteDarkness: 1.0;
uniform float vignetteOffset: 1.0;
#endif
uniform float exposure : 1.0;
uniform float bloomIntensity : 0.25;
uniform float lensflareIntensity : 1;
varying vec2 v_Texcoord;
@import clay.util.srgb
vec3 ACESToneMapping(vec3 color)
{
 const float A = 2.51;
 const float B = 0.03;
 const float C = 2.43;
 const float D = 0.59;
 const float E = 0.14;
 return (color * (A * color + B)) / (color * (C * color + D) + E);
}
float eyeAdaption(float fLum)
{
 return mix(0.2, fLum, 0.5);
}
#ifdef LUT_ENABLED
vec3 lutTransform(vec3 color) {
 float blueColor = color.b * 63.0;
 vec2 quad1;
 quad1.y = floor(floor(blueColor) / 8.0);
 quad1.x = floor(blueColor) - (quad1.y * 8.0);
 vec2 quad2;
 quad2.y = floor(ceil(blueColor) / 8.0);
 quad2.x = ceil(blueColor) - (quad2.y * 8.0);
 vec2 texPos1;
 texPos1.x = (quad1.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.r);
 texPos1.y = (quad1.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.g);
 vec2 texPos2;
 texPos2.x = (quad2.x * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.r);
 texPos2.y = (quad2.y * 0.125) + 0.5/512.0 + ((0.125 - 1.0/512.0) * color.g);
 vec4 newColor1 = texture2D(lut, texPos1);
 vec4 newColor2 = texture2D(lut, texPos2);
 vec4 newColor = mix(newColor1, newColor2, fract(blueColor));
 return newColor.rgb;
}
#endif
@import clay.util.rgbm
void main()
{
 vec4 texel = vec4(0.0);
 vec4 originalTexel = vec4(0.0);
#ifdef TEXTURE_ENABLED
 texel = decodeHDR(texture2D(texture, v_Texcoord));
 originalTexel = texel;
#endif
#ifdef BLOOM_ENABLED
 vec4 bloomTexel = decodeHDR(texture2D(bloom, v_Texcoord));
 texel.rgb += bloomTexel.rgb * bloomIntensity;
 texel.a += bloomTexel.a * bloomIntensity;
#endif
#ifdef LENSFLARE_ENABLED
 texel += decodeHDR(texture2D(lensflare, v_Texcoord)) * texture2D(lensdirt, v_Texcoord) * lensflareIntensity;
#endif
 texel.a = min(texel.a, 1.0);
#ifdef LUM_ENABLED
 float fLum = texture2D(lum, vec2(0.5, 0.5)).r;
 float adaptedLumDest = 3.0 / (max(0.1, 1.0 + 10.0*eyeAdaption(fLum)));
 float exposureBias = adaptedLumDest * exposure;
#else
 float exposureBias = exposure;
#endif
#ifdef TONEMAPPING
 texel.rgb *= exposureBias;
 texel.rgb = ACESToneMapping(texel.rgb);
#endif
 texel = linearTosRGB(texel);
#ifdef LUT_ENABLED
 texel.rgb = lutTransform(clamp(texel.rgb,vec3(0.0),vec3(1.0)));
#endif
#ifdef COLOR_CORRECTION
 texel.rgb = clamp(texel.rgb + vec3(brightness), 0.0, 1.0);
 texel.rgb = clamp((texel.rgb - vec3(0.5))*contrast+vec3(0.5), 0.0, 1.0);
 float lum = dot(texel.rgb, vec3(0.2125, 0.7154, 0.0721));
 texel.rgb = mix(vec3(lum), texel.rgb, saturation);
#endif
#ifdef VIGNETTE
 vec2 uv = (v_Texcoord - vec2(0.5)) * vec2(vignetteOffset);
 texel.rgb = mix(texel.rgb, vec3(1.0 - vignetteDarkness), dot(uv, uv));
#endif
 gl_FragColor = encodeHDR(texel);
#ifdef DEBUG
 #if DEBUG == 1
 gl_FragColor = encodeHDR(decodeHDR(texture2D(texture, v_Texcoord)));
 #elif DEBUG == 2
 gl_FragColor = encodeHDR(decodeHDR(texture2D(bloom, v_Texcoord)) * bloomIntensity);
 #elif DEBUG == 3
 gl_FragColor = encodeHDR(decodeHDR(texture2D(lensflare, v_Texcoord) * lensflareIntensity));
 #endif
#endif
 if (originalTexel.a <= 0.01 && gl_FragColor.a > 1e-5) {
 gl_FragColor.a = dot(gl_FragColor.rgb, vec3(0.2125, 0.7154, 0.0721));
 }
#ifdef PREMULTIPLY_ALPHA
 gl_FragColor.rgb *= gl_FragColor.a;
#endif
}
@end`,nu=`@export clay.compositor.lensflare
#define SAMPLE_NUMBER 8
uniform sampler2D texture;
uniform sampler2D lenscolor;
uniform vec2 textureSize : [512, 512];
uniform float dispersal : 0.3;
uniform float haloWidth : 0.4;
uniform float distortion : 1.0;
varying vec2 v_Texcoord;
@import clay.util.rgbm
vec4 textureDistorted(
 in vec2 texcoord,
 in vec2 direction,
 in vec3 distortion
) {
 return vec4(
 decodeHDR(texture2D(texture, texcoord + direction * distortion.r)).r,
 decodeHDR(texture2D(texture, texcoord + direction * distortion.g)).g,
 decodeHDR(texture2D(texture, texcoord + direction * distortion.b)).b,
 1.0
 );
}
void main()
{
 vec2 texcoord = -v_Texcoord + vec2(1.0); vec2 textureOffset = 1.0 / textureSize;
 vec2 ghostVec = (vec2(0.5) - texcoord) * dispersal;
 vec2 haloVec = normalize(ghostVec) * haloWidth;
 vec3 distortion = vec3(-textureOffset.x * distortion, 0.0, textureOffset.x * distortion);
 vec4 result = vec4(0.0);
 for (int i = 0; i < SAMPLE_NUMBER; i++)
 {
 vec2 offset = fract(texcoord + ghostVec * float(i));
 float weight = length(vec2(0.5) - offset) / length(vec2(0.5));
 weight = pow(1.0 - weight, 10.0);
 result += textureDistorted(offset, normalize(ghostVec), distortion) * weight;
 }
 result *= texture2D(lenscolor, vec2(length(vec2(0.5) - texcoord)) / length(vec2(0.5)));
 float weight = length(vec2(0.5) - fract(texcoord + haloVec)) / length(vec2(0.5));
 weight = pow(1.0 - weight, 10.0);
 vec2 offset = fract(texcoord + haloVec);
 result += textureDistorted(offset, normalize(ghostVec), distortion) * weight;
 gl_FragColor = result;
}
@end`,Fa=`@export clay.compositor.blend
#define SHADER_NAME blend
#ifdef TEXTURE1_ENABLED
uniform sampler2D texture1;
uniform float weight1 : 1.0;
#endif
#ifdef TEXTURE2_ENABLED
uniform sampler2D texture2;
uniform float weight2 : 1.0;
#endif
#ifdef TEXTURE3_ENABLED
uniform sampler2D texture3;
uniform float weight3 : 1.0;
#endif
#ifdef TEXTURE4_ENABLED
uniform sampler2D texture4;
uniform float weight4 : 1.0;
#endif
#ifdef TEXTURE5_ENABLED
uniform sampler2D texture5;
uniform float weight5 : 1.0;
#endif
#ifdef TEXTURE6_ENABLED
uniform sampler2D texture6;
uniform float weight6 : 1.0;
#endif
varying vec2 v_Texcoord;
@import clay.util.rgbm
void main()
{
 vec4 tex = vec4(0.0);
#ifdef TEXTURE1_ENABLED
 tex += decodeHDR(texture2D(texture1, v_Texcoord)) * weight1;
#endif
#ifdef TEXTURE2_ENABLED
 tex += decodeHDR(texture2D(texture2, v_Texcoord)) * weight2;
#endif
#ifdef TEXTURE3_ENABLED
 tex += decodeHDR(texture2D(texture3, v_Texcoord)) * weight3;
#endif
#ifdef TEXTURE4_ENABLED
 tex += decodeHDR(texture2D(texture4, v_Texcoord)) * weight4;
#endif
#ifdef TEXTURE5_ENABLED
 tex += decodeHDR(texture2D(texture5, v_Texcoord)) * weight5;
#endif
#ifdef TEXTURE6_ENABLED
 tex += decodeHDR(texture2D(texture6, v_Texcoord)) * weight6;
#endif
 gl_FragColor = encodeHDR(tex);
}
@end`,Ua=`@export clay.compositor.fxaa
uniform sampler2D texture;
uniform vec4 viewport : VIEWPORT;
varying vec2 v_Texcoord;
#define FXAA_REDUCE_MIN (1.0/128.0)
#define FXAA_REDUCE_MUL (1.0/8.0)
#define FXAA_SPAN_MAX 8.0
@import clay.util.rgbm
void main()
{
 vec2 resolution = 1.0 / viewport.zw;
 vec3 rgbNW = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( -1.0, -1.0 ) ) * resolution ) ).xyz;
 vec3 rgbNE = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( 1.0, -1.0 ) ) * resolution ) ).xyz;
 vec3 rgbSW = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( -1.0, 1.0 ) ) * resolution ) ).xyz;
 vec3 rgbSE = decodeHDR( texture2D( texture, ( gl_FragCoord.xy + vec2( 1.0, 1.0 ) ) * resolution ) ).xyz;
 vec4 rgbaM = decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution ) );
 vec3 rgbM = rgbaM.xyz;
 float opacity = rgbaM.w;
 vec3 luma = vec3( 0.299, 0.587, 0.114 );
 float lumaNW = dot( rgbNW, luma );
 float lumaNE = dot( rgbNE, luma );
 float lumaSW = dot( rgbSW, luma );
 float lumaSE = dot( rgbSE, luma );
 float lumaM = dot( rgbM, luma );
 float lumaMin = min( lumaM, min( min( lumaNW, lumaNE ), min( lumaSW, lumaSE ) ) );
 float lumaMax = max( lumaM, max( max( lumaNW, lumaNE) , max( lumaSW, lumaSE ) ) );
 vec2 dir;
 dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));
 dir.y = ((lumaNW + lumaSW) - (lumaNE + lumaSE));
 float dirReduce = max( ( lumaNW + lumaNE + lumaSW + lumaSE ) * ( 0.25 * FXAA_REDUCE_MUL ), FXAA_REDUCE_MIN );
 float rcpDirMin = 1.0 / ( min( abs( dir.x ), abs( dir.y ) ) + dirReduce );
 dir = min( vec2( FXAA_SPAN_MAX, FXAA_SPAN_MAX),
 max( vec2(-FXAA_SPAN_MAX, -FXAA_SPAN_MAX),
 dir * rcpDirMin)) * resolution;
 vec3 rgbA = decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * ( 1.0 / 3.0 - 0.5 ) ) ).xyz;
 rgbA += decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * ( 2.0 / 3.0 - 0.5 ) ) ).xyz;
 rgbA *= 0.5;
 vec3 rgbB = decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * -0.5 ) ).xyz;
 rgbB += decodeHDR( texture2D( texture, gl_FragCoord.xy * resolution + dir * 0.5 ) ).xyz;
 rgbB *= 0.25;
 rgbB += rgbA * 0.5;
 float lumaB = dot( rgbB, luma );
 if ( ( lumaB < lumaMin ) || ( lumaB > lumaMax ) )
 {
 gl_FragColor = vec4( rgbA, opacity );
 }
 else {
 gl_FragColor = vec4( rgbB, opacity );
 }
}
@end`;function au(e){e.import(tu),e.import(Da),e.import(ru),e.import(Pa),e.import(iu),e.import(Na),e.import(Ra),e.import(Oa),e.import(Ia),e.import(Ba),e.import(nu),e.import(Fa),e.import(Ua)}au(z);var ou=/^#source\((.*?)\)/;function su(e,t){var r=new Ql;t=t||{};var i={textures:{},parameters:{}},n=function(s,l){for(var u=0;u<e.nodes.length;u++){var f=e.nodes[u],h=lu(f,i,t);h&&r.addNode(h)}};for(var a in e.parameters){var o=e.parameters[a];i.parameters[a]=zi(o)}return hu(e,i,t,function(s){i.textures=s,n()}),r}function lu(e,t,r){var i=e.type||"filter",n,a,o;if(i==="filter"){var s=e.shader.trim(),l=ou.exec(s);if(l?n=z.source(l[1].trim()):s.charAt(0)==="#"&&(n=t.shaders[s.substr(1)]),n||(n=s),!n)return}if(e.inputs){a={};for(var u in e.inputs)typeof e.inputs[u]=="string"?a[u]=e.inputs[u]:a[u]={node:e.inputs[u].node,pin:e.inputs[u].pin}}if(e.outputs){o={};for(var u in e.outputs){var f=e.outputs[u];o[u]={},f.attachment!=null&&(o[u].attachment=f.attachment),f.keepLastFrame!=null&&(o[u].keepLastFrame=f.keepLastFrame),f.outputLastFrame!=null&&(o[u].outputLastFrame=f.outputLastFrame),f.parameters&&(o[u].parameters=zi(f.parameters))}}var h;if(i==="scene"?h=new Jl({name:e.name,scene:r.scene,camera:r.camera,outputs:o}):i==="texture"?h=new $l({name:e.name,outputs:o}):h=new eu({name:e.name,shader:n,inputs:a,outputs:o}),h){if(e.parameters)for(var u in e.parameters){var d=e.parameters[u];typeof d=="string"?(d=d.trim(),d.charAt(0)==="#"?d=t.textures[d.substr(1)]:h.on("beforerender",cu(u,za(d)))):typeof d=="function"&&h.on("beforerender",d),h.setParameter(u,d)}if(e.defines&&h.pass)for(var u in e.defines){var d=e.defines[u];h.pass.material.define("fragment",u,d)}}return h}function uu(e,t){return e}function fu(e,t){return t}function zi(e){var t={};if(!e)return t;["type","minFilter","magFilter","wrapS","wrapT","flipY","useMipmap"].forEach(function(i){var n=e[i];n!=null&&(typeof n=="string"&&(n=O[n]),t[i]=n)});var r=e.scale||1;return["width","height"].forEach(function(i){if(e[i]!=null){var n=e[i];typeof n=="string"?(n=n.trim(),t[i]=du(i,za(n),r)):t[i]=n}}),t.width||(t.width=uu),t.height||(t.height=fu),e.useMipmap!=null&&(t.useMipmap=e.useMipmap),t}function hu(e,t,r,i){if(!e.textures){i({});return}var n={},a=0,o=!1,s=r.textureRootPath;he.each(e.textures,function(l,u){var f,h=l.path,d=zi(l.parameters);if(Array.isArray(h)&&h.length===6)s&&(h=h.map(function(c){return he.relative2absolute(c,s)})),f=new At(d);else if(typeof h=="string")s&&(h=he.relative2absolute(h,s)),f=new K(d);else return;f.load(h),a++,f.once("success",function(){n[u]=f,a--,a===0&&(i(n),o=!0)})}),a===0&&!o&&i(n)}function cu(e,t){return function(r){var i=r.getDevicePixelRatio(),n=r.getWidth(),a=r.getHeight(),o=t(n,a,i);this.setParameter(e,o)}}function du(e,t,r){return r=r||1,function(i){var n=i.getDevicePixelRatio(),a=i.getWidth()*r,o=i.getHeight()*r;return t(a,o,n)}}function za(e){var t=/^expr\((.*)\)$/.exec(e);if(t)try{var r=new Function("width","height","dpr","return "+t[1]);return r(1,1),r}catch{throw new Error("Invalid expression.")}}function Xt(e,t){for(var r=0,i=1/t,n=e;n>0;)r=r+i*(n%t),n=Math.floor(n/t),i=i/t;return r}const vu=`@export ecgl.ssao.estimate

uniform sampler2D depthTex;

uniform sampler2D normalTex;

uniform sampler2D noiseTex;

uniform vec2 depthTexSize;

uniform vec2 noiseTexSize;

uniform mat4 projection;

uniform mat4 projectionInv;

uniform mat4 viewInverseTranspose;

uniform vec3 kernel[KERNEL_SIZE];

uniform float radius : 1;

uniform float power : 1;

uniform float bias: 1e-2;

uniform float intensity: 1.0;

varying vec2 v_Texcoord;

float ssaoEstimator(in vec3 originPos, in mat3 kernelBasis) {
 float occlusion = 0.0;

 for (int i = 0; i < KERNEL_SIZE; i++) {
 vec3 samplePos = kernel[i];
#ifdef NORMALTEX_ENABLED
 samplePos = kernelBasis * samplePos;
#endif
 samplePos = samplePos * radius + originPos;

 vec4 texCoord = projection * vec4(samplePos, 1.0);
 texCoord.xy /= texCoord.w;

 vec4 depthTexel = texture2D(depthTex, texCoord.xy * 0.5 + 0.5);

 float sampleDepth = depthTexel.r * 2.0 - 1.0;
 if (projection[3][3] == 0.0) {
 sampleDepth = projection[3][2] / (sampleDepth * projection[2][3] - projection[2][2]);
 }
 else {
 sampleDepth = (sampleDepth - projection[3][2]) / projection[2][2];
 }
 
 float rangeCheck = smoothstep(0.0, 1.0, radius / abs(originPos.z - sampleDepth));
 occlusion += rangeCheck * step(samplePos.z, sampleDepth - bias);
 }
#ifdef NORMALTEX_ENABLED
 occlusion = 1.0 - occlusion / float(KERNEL_SIZE);
#else
 occlusion = 1.0 - clamp((occlusion / float(KERNEL_SIZE) - 0.6) * 2.5, 0.0, 1.0);
#endif
 return pow(occlusion, power);
}

void main()
{

 vec4 depthTexel = texture2D(depthTex, v_Texcoord);

#ifdef NORMALTEX_ENABLED
 vec4 tex = texture2D(normalTex, v_Texcoord);
 if (dot(tex.rgb, tex.rgb) == 0.0) {
 gl_FragColor = vec4(1.0);
 return;
 }
 vec3 N = tex.rgb * 2.0 - 1.0;
 N = (viewInverseTranspose * vec4(N, 0.0)).xyz;

 vec2 noiseTexCoord = depthTexSize / vec2(noiseTexSize) * v_Texcoord;
 vec3 rvec = texture2D(noiseTex, noiseTexCoord).rgb * 2.0 - 1.0;
 vec3 T = normalize(rvec - N * dot(rvec, N));
 vec3 BT = normalize(cross(N, T));
 mat3 kernelBasis = mat3(T, BT, N);
#else
 if (depthTexel.r > 0.99999) {
 gl_FragColor = vec4(1.0);
 return;
 }
 mat3 kernelBasis;
#endif

 float z = depthTexel.r * 2.0 - 1.0;

 vec4 projectedPos = vec4(v_Texcoord * 2.0 - 1.0, z, 1.0);
 vec4 p4 = projectionInv * projectedPos;

 vec3 position = p4.xyz / p4.w;

 float ao = ssaoEstimator(position, kernelBasis);
 ao = clamp(1.0 - (1.0 - ao) * intensity, 0.0, 1.0);
 gl_FragColor = vec4(vec3(ao), 1.0);
}

@end


@export ecgl.ssao.blur
#define SHADER_NAME SSAO_BLUR

uniform sampler2D ssaoTexture;

#ifdef NORMALTEX_ENABLED
uniform sampler2D normalTex;
#endif

varying vec2 v_Texcoord;

uniform vec2 textureSize;
uniform float blurSize : 1.0;

uniform int direction: 0.0;

#ifdef DEPTHTEX_ENABLED
uniform sampler2D depthTex;
uniform mat4 projection;
uniform float depthRange : 0.5;

float getLinearDepth(vec2 coord)
{
 float depth = texture2D(depthTex, coord).r * 2.0 - 1.0;
 return projection[3][2] / (depth * projection[2][3] - projection[2][2]);
}
#endif

void main()
{
 float kernel[5];
 kernel[0] = 0.122581;
 kernel[1] = 0.233062;
 kernel[2] = 0.288713;
 kernel[3] = 0.233062;
 kernel[4] = 0.122581;

 vec2 off = vec2(0.0);
 if (direction == 0) {
 off[0] = blurSize / textureSize.x;
 }
 else {
 off[1] = blurSize / textureSize.y;
 }

 vec2 coord = v_Texcoord;

 float sum = 0.0;
 float weightAll = 0.0;

#ifdef NORMALTEX_ENABLED
 vec3 centerNormal = texture2D(normalTex, v_Texcoord).rgb * 2.0 - 1.0;
#endif
#if defined(DEPTHTEX_ENABLED)
 float centerDepth = getLinearDepth(v_Texcoord);
#endif

 for (int i = 0; i < 5; i++) {
 vec2 coord = clamp(v_Texcoord + vec2(float(i) - 2.0) * off, vec2(0.0), vec2(1.0));

 float w = kernel[i];
#ifdef NORMALTEX_ENABLED
 vec3 normal = texture2D(normalTex, coord).rgb * 2.0 - 1.0;
 w *= clamp(dot(normal, centerNormal), 0.0, 1.0);
#endif
#ifdef DEPTHTEX_ENABLED
 float d = getLinearDepth(coord);
 w *= (1.0 - smoothstep(abs(centerDepth - d) / depthRange, 0.0, 1.0));
#endif

 weightAll += w;
 sum += texture2D(ssaoTexture, coord).r * w;
 }

 gl_FragColor = vec4(vec3(sum / weightAll), 1.0);
}

@end
`;z.import(vu);function Ha(e){for(var t=new Uint8Array(e*e*4),r=0,i=new b,n=0;n<e;n++)for(var a=0;a<e;a++)i.set(Math.random()*2-1,Math.random()*2-1,0).normalize(),t[r++]=(i.x*.5+.5)*255,t[r++]=(i.y*.5+.5)*255,t[r++]=0,t[r++]=255;return t}function kn(e){return new K({pixels:Ha(e),wrapS:O.REPEAT,wrapT:O.REPEAT,width:e,height:e})}function pu(e,t,r){var i=new Float32Array(e*3);t=t||0;for(var n=0;n<e;n++){var a=Xt(n+t,2)*(r?1:2)*Math.PI,o=Xt(n+t,3)*Math.PI,s=Math.random(),l=Math.cos(a)*Math.sin(o)*s,u=Math.cos(o)*s,f=Math.sin(a)*Math.sin(o)*s;i[n*3]=l,i[n*3+1]=u,i[n*3+2]=f}return i}function ot(e){e=e||{},this._ssaoPass=new Me({fragment:z.source("ecgl.ssao.estimate")}),this._blurPass=new Me({fragment:z.source("ecgl.ssao.blur")}),this._framebuffer=new me({depthBuffer:!1}),this._ssaoTexture=new K,this._blurTexture=new K,this._blurTexture2=new K,this._depthTex=e.depthTexture,this._normalTex=e.normalTexture,this.setNoiseSize(4),this.setKernelSize(e.kernelSize||12),e.radius!=null&&this.setParameter("radius",e.radius),e.power!=null&&this.setParameter("power",e.power),this._normalTex||(this._ssaoPass.material.disableTexture("normalTex"),this._blurPass.material.disableTexture("normalTex")),this._depthTex||this._blurPass.material.disableTexture("depthTex"),this._blurPass.material.setUniform("normalTex",this._normalTex),this._blurPass.material.setUniform("depthTex",this._depthTex)}ot.prototype.setDepthTexture=function(e){this._depthTex=e};ot.prototype.setNormalTexture=function(e){this._normalTex=e,this._ssaoPass.material[e?"enableTexture":"disableTexture"]("normalTex"),this.setKernelSize(this._kernelSize)};ot.prototype.update=function(e,t,r){var i=e.getWidth(),n=e.getHeight(),a=this._ssaoPass,o=this._blurPass;a.setUniform("kernel",this._kernels[r%this._kernels.length]),a.setUniform("depthTex",this._depthTex),this._normalTex!=null&&a.setUniform("normalTex",this._normalTex),a.setUniform("depthTexSize",[this._depthTex.width,this._depthTex.height]);var s=new F;F.transpose(s,t.worldTransform),a.setUniform("projection",t.projectionMatrix.array),a.setUniform("projectionInv",t.invProjectionMatrix.array),a.setUniform("viewInverseTranspose",s.array);var l=this._ssaoTexture,u=this._blurTexture,f=this._blurTexture2;l.width=i/2,l.height=n/2,u.width=i,u.height=n,f.width=i,f.height=n,this._framebuffer.attach(l),this._framebuffer.bind(e),e.gl.clearColor(1,1,1,1),e.gl.clear(e.gl.COLOR_BUFFER_BIT),a.render(e),o.setUniform("textureSize",[i/2,n/2]),o.setUniform("projection",t.projectionMatrix.array),this._framebuffer.attach(u),o.setUniform("direction",0),o.setUniform("ssaoTexture",l),o.render(e),this._framebuffer.attach(f),o.setUniform("textureSize",[i,n]),o.setUniform("direction",1),o.setUniform("ssaoTexture",u),o.render(e),this._framebuffer.unbind(e);var h=e.clearColor;e.gl.clearColor(h[0],h[1],h[2],h[3])};ot.prototype.getTargetTexture=function(){return this._blurTexture2};ot.prototype.setParameter=function(e,t){e==="noiseTexSize"?this.setNoiseSize(t):e==="kernelSize"?this.setKernelSize(t):e==="intensity"?this._ssaoPass.material.set("intensity",t):this._ssaoPass.setUniform(e,t)};ot.prototype.setKernelSize=function(e){this._kernelSize=e,this._ssaoPass.material.define("fragment","KERNEL_SIZE",e),this._kernels=this._kernels||[];for(var t=0;t<30;t++)this._kernels[t]=pu(e,t*e,!!this._normalTex)};ot.prototype.setNoiseSize=function(e){var t=this._ssaoPass.getUniform("noiseTex");t?(t.data=Ha(e),t.width=t.height=e,t.dirty()):(t=kn(e),this._ssaoPass.setUniform("noiseTex",kn(e))),this._ssaoPass.setUniform("noiseTexSize",[e,e])};ot.prototype.dispose=function(e){this._blurTexture.dispose(e),this._ssaoTexture.dispose(e),this._blurTexture2.dispose(e)};const mu=`@export ecgl.ssr.main

#define SHADER_NAME SSR
#define MAX_ITERATION 20;
#define SAMPLE_PER_FRAME 5;
#define TOTAL_SAMPLES 128;

uniform sampler2D sourceTexture;
uniform sampler2D gBufferTexture1;
uniform sampler2D gBufferTexture2;
uniform sampler2D gBufferTexture3;
uniform samplerCube specularCubemap;
uniform float specularIntensity: 1;

uniform mat4 projection;
uniform mat4 projectionInv;
uniform mat4 toViewSpace;
uniform mat4 toWorldSpace;

uniform float maxRayDistance: 200;

uniform float pixelStride: 16;
uniform float pixelStrideZCutoff: 50; 
uniform float screenEdgeFadeStart: 0.9; 
uniform float eyeFadeStart : 0.2; uniform float eyeFadeEnd: 0.8; 
uniform float minGlossiness: 0.2; uniform float zThicknessThreshold: 1;

uniform float nearZ;
uniform vec2 viewportSize : VIEWPORT_SIZE;

uniform float jitterOffset: 0;

varying vec2 v_Texcoord;

#ifdef DEPTH_DECODE
@import clay.util.decode_float
#endif

#ifdef PHYSICALLY_CORRECT
uniform sampler2D normalDistribution;
uniform float sampleOffset: 0;
uniform vec2 normalDistributionSize;

vec3 transformNormal(vec3 H, vec3 N) {
 vec3 upVector = N.y > 0.999 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0);
 vec3 tangentX = normalize(cross(N, upVector));
 vec3 tangentZ = cross(N, tangentX);
 return normalize(tangentX * H.x + N * H.y + tangentZ * H.z);
}
vec3 importanceSampleNormalGGX(float i, float roughness, vec3 N) {
 float p = fract((i + sampleOffset) / float(TOTAL_SAMPLES));
 vec3 H = texture2D(normalDistribution,vec2(roughness, p)).rgb;
 return transformNormal(H, N);
}
float G_Smith(float g, float ndv, float ndl) {
 float roughness = 1.0 - g;
 float k = roughness * roughness / 2.0;
 float G1V = ndv / (ndv * (1.0 - k) + k);
 float G1L = ndl / (ndl * (1.0 - k) + k);
 return G1L * G1V;
}
vec3 F_Schlick(float ndv, vec3 spec) {
 return spec + (1.0 - spec) * pow(1.0 - ndv, 5.0);
}
#endif

float fetchDepth(sampler2D depthTexture, vec2 uv)
{
 vec4 depthTexel = texture2D(depthTexture, uv);
 return depthTexel.r * 2.0 - 1.0;
}

float linearDepth(float depth)
{
 if (projection[3][3] == 0.0) {
 return projection[3][2] / (depth * projection[2][3] - projection[2][2]);
 }
 else {
 return (depth - projection[3][2]) / projection[2][2];
 }
}

bool rayIntersectDepth(float rayZNear, float rayZFar, vec2 hitPixel)
{
 if (rayZFar > rayZNear)
 {
 float t = rayZFar; rayZFar = rayZNear; rayZNear = t;
 }
 float cameraZ = linearDepth(fetchDepth(gBufferTexture2, hitPixel));
 return rayZFar <= cameraZ && rayZNear >= cameraZ - zThicknessThreshold;
}


bool traceScreenSpaceRay(
 vec3 rayOrigin, vec3 rayDir, float jitter,
 out vec2 hitPixel, out vec3 hitPoint, out float iterationCount
)
{
 float rayLength = ((rayOrigin.z + rayDir.z * maxRayDistance) > -nearZ)
 ? (-nearZ - rayOrigin.z) / rayDir.z : maxRayDistance;

 vec3 rayEnd = rayOrigin + rayDir * rayLength;

 vec4 H0 = projection * vec4(rayOrigin, 1.0);
 vec4 H1 = projection * vec4(rayEnd, 1.0);

 float k0 = 1.0 / H0.w, k1 = 1.0 / H1.w;

 vec3 Q0 = rayOrigin * k0, Q1 = rayEnd * k1;

 vec2 P0 = (H0.xy * k0 * 0.5 + 0.5) * viewportSize;
 vec2 P1 = (H1.xy * k1 * 0.5 + 0.5) * viewportSize;

 P1 += dot(P1 - P0, P1 - P0) < 0.0001 ? 0.01 : 0.0;
 vec2 delta = P1 - P0;

 bool permute = false;
 if (abs(delta.x) < abs(delta.y)) {
 permute = true;
 delta = delta.yx;
 P0 = P0.yx;
 P1 = P1.yx;
 }
 float stepDir = sign(delta.x);
 float invdx = stepDir / delta.x;

 vec3 dQ = (Q1 - Q0) * invdx;
 float dk = (k1 - k0) * invdx;

 vec2 dP = vec2(stepDir, delta.y * invdx);

 float strideScaler = 1.0 - min(1.0, -rayOrigin.z / pixelStrideZCutoff);
 float pixStride = 1.0 + strideScaler * pixelStride;

 dP *= pixStride; dQ *= pixStride; dk *= pixStride;

 vec4 pqk = vec4(P0, Q0.z, k0);
 vec4 dPQK = vec4(dP, dQ.z, dk);

 pqk += dPQK * jitter;
 float rayZFar = (dPQK.z * 0.5 + pqk.z) / (dPQK.w * 0.5 + pqk.w);
 float rayZNear;

 bool intersect = false;

 vec2 texelSize = 1.0 / viewportSize;

 iterationCount = 0.0;

 for (int i = 0; i < MAX_ITERATION; i++)
 {
 pqk += dPQK;

 rayZNear = rayZFar;
 rayZFar = (dPQK.z * 0.5 + pqk.z) / (dPQK.w * 0.5 + pqk.w);

 hitPixel = permute ? pqk.yx : pqk.xy;
 hitPixel *= texelSize;

 intersect = rayIntersectDepth(rayZNear, rayZFar, hitPixel);

 iterationCount += 1.0;

 dPQK *= 1.2;

 if (intersect) {
 break;
 }
 }

 Q0.xy += dQ.xy * iterationCount;
 Q0.z = pqk.z;
 hitPoint = Q0 / pqk.w;

 return intersect;
}

float calculateAlpha(
 float iterationCount, float reflectivity,
 vec2 hitPixel, vec3 hitPoint, float dist, vec3 rayDir
)
{
 float alpha = clamp(reflectivity, 0.0, 1.0);
 alpha *= 1.0 - (iterationCount / float(MAX_ITERATION));
 vec2 hitPixelNDC = hitPixel * 2.0 - 1.0;
 float maxDimension = min(1.0, max(abs(hitPixelNDC.x), abs(hitPixelNDC.y)));
 alpha *= 1.0 - max(0.0, maxDimension - screenEdgeFadeStart) / (1.0 - screenEdgeFadeStart);

 float _eyeFadeStart = eyeFadeStart;
 float _eyeFadeEnd = eyeFadeEnd;
 if (_eyeFadeStart > _eyeFadeEnd) {
 float tmp = _eyeFadeEnd;
 _eyeFadeEnd = _eyeFadeStart;
 _eyeFadeStart = tmp;
 }

 float eyeDir = clamp(rayDir.z, _eyeFadeStart, _eyeFadeEnd);
 alpha *= 1.0 - (eyeDir - _eyeFadeStart) / (_eyeFadeEnd - _eyeFadeStart);

 alpha *= 1.0 - clamp(dist / maxRayDistance, 0.0, 1.0);

 return alpha;
}

@import clay.util.rand

@import clay.util.rgbm

void main()
{
 vec4 normalAndGloss = texture2D(gBufferTexture1, v_Texcoord);

 if (dot(normalAndGloss.rgb, vec3(1.0)) == 0.0) {
 discard;
 }

 float g = normalAndGloss.a;
#if !defined(PHYSICALLY_CORRECT)
 if (g <= minGlossiness) {
 discard;
 }
#endif

 float reflectivity = (g - minGlossiness) / (1.0 - minGlossiness);

 vec3 N = normalize(normalAndGloss.rgb * 2.0 - 1.0);
 N = normalize((toViewSpace * vec4(N, 0.0)).xyz);

 vec4 projectedPos = vec4(v_Texcoord * 2.0 - 1.0, fetchDepth(gBufferTexture2, v_Texcoord), 1.0);
 vec4 pos = projectionInv * projectedPos;
 vec3 rayOrigin = pos.xyz / pos.w;
 vec3 V = -normalize(rayOrigin);

 float ndv = clamp(dot(N, V), 0.0, 1.0);
 float iterationCount;
 float jitter = rand(fract(v_Texcoord + jitterOffset));

#ifdef PHYSICALLY_CORRECT
 vec4 color = vec4(vec3(0.0), 1.0);
 vec4 albedoMetalness = texture2D(gBufferTexture3, v_Texcoord);
 vec3 albedo = albedoMetalness.rgb;
 float m = albedoMetalness.a;
 vec3 diffuseColor = albedo * (1.0 - m);
 vec3 spec = mix(vec3(0.04), albedo, m);

 float jitter2 = rand(fract(v_Texcoord)) * float(TOTAL_SAMPLES);

 for (int i = 0; i < SAMPLE_PER_FRAME; i++) {
 vec3 H = importanceSampleNormalGGX(float(i) + jitter2, 1.0 - g, N);
 vec3 rayDir = normalize(reflect(-V, H));
#else
 vec3 rayDir = normalize(reflect(-V, N));
#endif
 vec2 hitPixel;
 vec3 hitPoint;

 bool intersect = traceScreenSpaceRay(rayOrigin, rayDir, jitter, hitPixel, hitPoint, iterationCount);

 float dist = distance(rayOrigin, hitPoint);

 vec3 hitNormal = texture2D(gBufferTexture1, hitPixel).rgb * 2.0 - 1.0;
 hitNormal = normalize((toViewSpace * vec4(hitNormal, 0.0)).xyz);
#ifdef PHYSICALLY_CORRECT
 float ndl = clamp(dot(N, rayDir), 0.0, 1.0);
 float vdh = clamp(dot(V, H), 0.0, 1.0);
 float ndh = clamp(dot(N, H), 0.0, 1.0);
 vec3 litTexel = vec3(0.0);
 if (dot(hitNormal, rayDir) < 0.0 && intersect) {
 litTexel = texture2D(sourceTexture, hitPixel).rgb;
 litTexel *= pow(clamp(1.0 - dist / 200.0, 0.0, 1.0), 3.0);

 }
 else {
 #ifdef SPECULARCUBEMAP_ENABLED
 vec3 rayDirW = normalize(toWorldSpace * vec4(rayDir, 0.0)).rgb;
 litTexel = RGBMDecode(textureCubeLodEXT(specularCubemap, rayDirW, 0.0), 8.12).rgb * specularIntensity;
#endif
 }
 color.rgb += ndl * litTexel * (
 F_Schlick(ndl, spec) * G_Smith(g, ndv, ndl) * vdh / (ndh * ndv + 0.001)
 );
 }
 color.rgb /= float(SAMPLE_PER_FRAME);
#else
 #if !defined(SPECULARCUBEMAP_ENABLED)
 if (dot(hitNormal, rayDir) >= 0.0) {
 discard;
 }
 if (!intersect) {
 discard;
 }
#endif
 float alpha = clamp(calculateAlpha(iterationCount, reflectivity, hitPixel, hitPoint, dist, rayDir), 0.0, 1.0);
 vec4 color = texture2D(sourceTexture, hitPixel);
 color.rgb *= alpha;

#ifdef SPECULARCUBEMAP_ENABLED
 vec3 rayDirW = normalize(toWorldSpace * vec4(rayDir, 0.0)).rgb;
 alpha = alpha * (intersect ? 1.0 : 0.0);
 float bias = (1.0 -g) * 5.0;
 color.rgb += (1.0 - alpha)
 * RGBMDecode(textureCubeLodEXT(specularCubemap, rayDirW, bias), 8.12).rgb
 * specularIntensity;
#endif

#endif

 gl_FragColor = encodeHDR(color);
}
@end

@export ecgl.ssr.blur

uniform sampler2D texture;
uniform sampler2D gBufferTexture1;
uniform sampler2D gBufferTexture2;
uniform mat4 projection;
uniform float depthRange : 0.05;

varying vec2 v_Texcoord;

uniform vec2 textureSize;
uniform float blurSize : 1.0;

#ifdef BLEND
 #ifdef SSAOTEX_ENABLED
uniform sampler2D ssaoTex;
 #endif
uniform sampler2D sourceTexture;
#endif

float getLinearDepth(vec2 coord)
{
 float depth = texture2D(gBufferTexture2, coord).r * 2.0 - 1.0;
 return projection[3][2] / (depth * projection[2][3] - projection[2][2]);
}

@import clay.util.rgbm


void main()
{
 @import clay.compositor.kernel.gaussian_9

 vec4 centerNTexel = texture2D(gBufferTexture1, v_Texcoord);
 float g = centerNTexel.a;
 float maxBlurSize = clamp(1.0 - g, 0.0, 1.0) * blurSize;
#ifdef VERTICAL
 vec2 off = vec2(0.0, maxBlurSize / textureSize.y);
#else
 vec2 off = vec2(maxBlurSize / textureSize.x, 0.0);
#endif

 vec2 coord = v_Texcoord;

 vec4 sum = vec4(0.0);
 float weightAll = 0.0;

 vec3 cN = centerNTexel.rgb * 2.0 - 1.0;
 float cD = getLinearDepth(v_Texcoord);
 for (int i = 0; i < 9; i++) {
 vec2 coord = clamp((float(i) - 4.0) * off + v_Texcoord, vec2(0.0), vec2(1.0));
 float w = gaussianKernel[i]
 * clamp(dot(cN, texture2D(gBufferTexture1, coord).rgb * 2.0 - 1.0), 0.0, 1.0);
 float d = getLinearDepth(coord);
 w *= (1.0 - smoothstep(abs(cD - d) / depthRange, 0.0, 1.0));

 weightAll += w;
 sum += decodeHDR(texture2D(texture, coord)) * w;
 }

#ifdef BLEND
 float aoFactor = 1.0;
 #ifdef SSAOTEX_ENABLED
 aoFactor = texture2D(ssaoTex, v_Texcoord).r;
 #endif
 gl_FragColor = encodeHDR(
 sum / weightAll * aoFactor + decodeHDR(texture2D(sourceTexture, v_Texcoord))
 );
#else
 gl_FragColor = encodeHDR(sum / weightAll);
#endif
}

@end`;z.import(mu);function st(e){e=e||{},this._ssrPass=new Me({fragment:z.source("ecgl.ssr.main"),clearColor:[0,0,0,0]}),this._blurPass1=new Me({fragment:z.source("ecgl.ssr.blur"),clearColor:[0,0,0,0]}),this._blurPass2=new Me({fragment:z.source("ecgl.ssr.blur"),clearColor:[0,0,0,0]}),this._blendPass=new Me({fragment:z.source("clay.compositor.blend")}),this._blendPass.material.disableTexturesAll(),this._blendPass.material.enableTexture(["texture1","texture2"]),this._ssrPass.setUniform("gBufferTexture1",e.normalTexture),this._ssrPass.setUniform("gBufferTexture2",e.depthTexture),this._blurPass1.setUniform("gBufferTexture1",e.normalTexture),this._blurPass1.setUniform("gBufferTexture2",e.depthTexture),this._blurPass2.setUniform("gBufferTexture1",e.normalTexture),this._blurPass2.setUniform("gBufferTexture2",e.depthTexture),this._blurPass2.material.define("fragment","VERTICAL"),this._blurPass2.material.define("fragment","BLEND"),this._ssrTexture=new K({type:O.HALF_FLOAT}),this._texture2=new K({type:O.HALF_FLOAT}),this._texture3=new K({type:O.HALF_FLOAT}),this._prevTexture=new K({type:O.HALF_FLOAT}),this._currentTexture=new K({type:O.HALF_FLOAT}),this._frameBuffer=new me({depthBuffer:!1}),this._normalDistribution=null,this._totalSamples=256,this._samplePerFrame=4,this._ssrPass.material.define("fragment","SAMPLE_PER_FRAME",this._samplePerFrame),this._ssrPass.material.define("fragment","TOTAL_SAMPLES",this._totalSamples),this._downScale=1}st.prototype.setAmbientCubemap=function(e,t){this._ssrPass.material.set("specularCubemap",e),this._ssrPass.material.set("specularIntensity",t);var r=e&&t;this._ssrPass.material[r?"enableTexture":"disableTexture"]("specularCubemap")};st.prototype.update=function(e,t,r,i){var n=e.getWidth(),a=e.getHeight(),o=this._ssrTexture,s=this._texture2,l=this._texture3;o.width=this._prevTexture.width=this._currentTexture.width=n/this._downScale,o.height=this._prevTexture.height=this._currentTexture.height=a/this._downScale,s.width=l.width=n,s.height=l.height=a;var u=this._frameBuffer,f=this._ssrPass,h=this._blurPass1,d=this._blurPass2,c=this._blendPass,v=new F,p=new F;F.transpose(v,t.worldTransform),F.transpose(p,t.viewMatrix),f.setUniform("sourceTexture",r),f.setUniform("projection",t.projectionMatrix.array),f.setUniform("projectionInv",t.invProjectionMatrix.array),f.setUniform("toViewSpace",v.array),f.setUniform("toWorldSpace",p.array),f.setUniform("nearZ",t.near);var m=i/this._totalSamples*this._samplePerFrame;if(f.setUniform("jitterOffset",m),f.setUniform("sampleOffset",i*this._samplePerFrame),h.setUniform("textureSize",[o.width,o.height]),d.setUniform("textureSize",[n,a]),d.setUniform("sourceTexture",r),h.setUniform("projection",t.projectionMatrix.array),d.setUniform("projection",t.projectionMatrix.array),u.attach(o),u.bind(e),f.render(e),this._physicallyCorrect&&(u.attach(this._currentTexture),c.setUniform("texture1",this._prevTexture),c.setUniform("texture2",o),c.material.set({weight1:i>=1?.95:0,weight2:i>=1?.05:1}),c.render(e)),u.attach(s),h.setUniform("texture",this._physicallyCorrect?this._currentTexture:o),h.render(e),u.attach(l),d.setUniform("texture",s),d.render(e),u.unbind(e),this._physicallyCorrect){var _=this._prevTexture;this._prevTexture=this._currentTexture,this._currentTexture=_}};st.prototype.getTargetTexture=function(){return this._texture3};st.prototype.setParameter=function(e,t){e==="maxIteration"?this._ssrPass.material.define("fragment","MAX_ITERATION",t):this._ssrPass.setUniform(e,t)};st.prototype.setPhysicallyCorrect=function(e){e?(this._normalDistribution||(this._normalDistribution=Qe.generateNormalDistribution(64,this._totalSamples)),this._ssrPass.material.define("fragment","PHYSICALLY_CORRECT"),this._ssrPass.material.set("normalDistribution",this._normalDistribution),this._ssrPass.material.set("normalDistributionSize",[64,this._totalSamples])):this._ssrPass.material.undefine("fragment","PHYSICALLY_CORRECT"),this._physicallyCorrect=e};st.prototype.setSSAOTexture=function(e){var t=this._blurPass2;e?(t.material.enableTexture("ssaoTex"),t.material.set("ssaoTex",e)):t.material.disableTexture("ssaoTex")};st.prototype.isFinished=function(e){return this._physicallyCorrect?e>this._totalSamples/this._samplePerFrame:!0};st.prototype.dispose=function(e){this._ssrTexture.dispose(e),this._texture2.dispose(e),this._texture3.dispose(e),this._prevTexture.dispose(e),this._currentTexture.dispose(e),this._frameBuffer.dispose(e)};const Wn=[0,0,-.321585265978,-.154972575841,.458126042375,.188473391593,.842080129861,.527766490688,.147304551086,-.659453822776,-.331943915203,-.940619700594,.0479226680259,.54812163202,.701581552186,-.709825561388,-.295436780218,.940589268233,-.901489676764,.237713156085,.973570876096,-.109899459384,-.866792314779,-.451805525005,.330975007087,.800048655954,-.344275183665,.381779221166,-.386139432542,-.437418421534,-.576478634965,-.0148463392551,.385798197415,-.262426961053,-.666302061145,.682427250835,-.628010632582,-.732836215494,.10163141741,-.987658134403,.711995289051,-.320024291314,.0296005138058,.950296523438,.0130612307608,-.351024443122,-.879596633704,-.10478487883,.435712737232,.504254490347,.779203817497,.206477676721,.388264289969,-.896736162545,-.153106280781,-.629203242522,-.245517550697,.657969239148,.126830499058,.26862328493,-.634888119007,-.302301223431,.617074219636,.779817204925],_u=`@export ecgl.normal.vertex

@import ecgl.common.transformUniforms

@import ecgl.common.uv.header

@import ecgl.common.attributes

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

@import ecgl.common.normalMap.vertexHeader

@import ecgl.common.vertexAnimation.header

void main()
{

 @import ecgl.common.vertexAnimation.main

 @import ecgl.common.uv.main

 v_Normal = normalize((worldInverseTranspose * vec4(normal, 0.0)).xyz);
 v_WorldPosition = (world * vec4(pos, 1.0)).xyz;

 @import ecgl.common.normalMap.vertexMain

 gl_Position = worldViewProjection * vec4(pos, 1.0);

}


@end


@export ecgl.normal.fragment

#define ROUGHNESS_CHANEL 0

uniform bool useBumpMap;
uniform bool useRoughnessMap;
uniform bool doubleSide;
uniform float roughness;

@import ecgl.common.uv.fragmentHeader

varying vec3 v_Normal;
varying vec3 v_WorldPosition;

uniform mat4 viewInverse : VIEWINVERSE;

@import ecgl.common.normalMap.fragmentHeader
@import ecgl.common.bumpMap.header

uniform sampler2D roughnessMap;

void main()
{
 vec3 N = v_Normal;
 
 bool flipNormal = false;
 if (doubleSide) {
 vec3 eyePos = viewInverse[3].xyz;
 vec3 V = normalize(eyePos - v_WorldPosition);

 if (dot(N, V) < 0.0) {
 flipNormal = true;
 }
 }

 @import ecgl.common.normalMap.fragmentMain

 if (useBumpMap) {
 N = bumpNormal(v_WorldPosition, v_Normal, N);
 }

 float g = 1.0 - roughness;

 if (useRoughnessMap) {
 float g2 = 1.0 - texture2D(roughnessMap, v_DetailTexcoord)[ROUGHNESS_CHANEL];
 g = clamp(g2 + (g - 0.5) * 2.0, 0.0, 1.0);
 }

 if (flipNormal) {
 N = -N;
 }

 gl_FragColor.rgb = (N.xyz + 1.0) * 0.5;
 gl_FragColor.a = g;
}
@end`;z.import(_u);function mi(e,t,r,i,n){var a=e.gl;t.setUniform(a,"1i",r,n),a.activeTexture(a.TEXTURE0+n),i.isRenderable()?i.bind(e):i.unbind(e)}function gu(e,t,r,i,n){var a,o,s,l,u=e.gl;return function(f,h,d){if(!(l&&l.material===f.material)){var c=f.material,v=f.__program,p=c.get("roughness");p==null&&(p=1);var m=c.get("normalMap")||t,_=c.get("roughnessMap"),x=c.get("bumpMap"),T=c.get("uvRepeat"),g=c.get("uvOffset"),E=c.get("detailUvRepeat"),S=c.get("detailUvOffset"),C=!!x&&c.isTextureEnabled("bumpMap"),A=!!_&&c.isTextureEnabled("roughnessMap"),N=c.isDefined("fragment","DOUBLE_SIDED");x=x||r,_=_||i,d!==h?(h.set("normalMap",m),h.set("bumpMap",x),h.set("roughnessMap",_),h.set("useBumpMap",C),h.set("useRoughnessMap",A),h.set("doubleSide",N),T!=null&&h.set("uvRepeat",T),g!=null&&h.set("uvOffset",g),E!=null&&h.set("detailUvRepeat",E),S!=null&&h.set("detailUvOffset",S),h.set("roughness",p)):(v.setUniform(u,"1f","roughness",p),a!==m&&mi(e,v,"normalMap",m,0),o!==x&&x&&mi(e,v,"bumpMap",x,1),s!==_&&_&&mi(e,v,"roughnessMap",_,2),T!=null&&v.setUniform(u,"2f","uvRepeat",T),g!=null&&v.setUniform(u,"2f","uvOffset",g),E!=null&&v.setUniform(u,"2f","detailUvRepeat",E),S!=null&&v.setUniform(u,"2f","detailUvOffset",S),v.setUniform(u,"1i","useBumpMap",+C),v.setUniform(u,"1i","useRoughnessMap",+A),v.setUniform(u,"1i","doubleSide",+N)),a=m,o=x,s=_,l=f}}}function Zt(e){this._depthTex=new K({format:O.DEPTH_COMPONENT,type:O.UNSIGNED_INT}),this._normalTex=new K({type:O.HALF_FLOAT}),this._framebuffer=new me,this._framebuffer.attach(this._normalTex),this._framebuffer.attach(this._depthTex,me.DEPTH_ATTACHMENT),this._normalMaterial=new at({shader:new z(z.source("ecgl.normal.vertex"),z.source("ecgl.normal.fragment"))}),this._normalMaterial.enableTexture(["normalMap","bumpMap","roughnessMap"]),this._defaultNormalMap=Ke.createBlank("#000"),this._defaultBumpMap=Ke.createBlank("#000"),this._defaultRoughessMap=Ke.createBlank("#000"),this._debugPass=new Me({fragment:z.source("clay.compositor.output")}),this._debugPass.setUniform("texture",this._normalTex),this._debugPass.material.undefine("fragment","OUTPUT_ALPHA")}Zt.prototype.getDepthTexture=function(){return this._depthTex};Zt.prototype.getNormalTexture=function(){return this._normalTex};Zt.prototype.update=function(e,t,r){var i=e.getWidth(),n=e.getHeight(),a=this._depthTex,o=this._normalTex,s=this._normalMaterial;a.width=i,a.height=n,o.width=i,o.height=n;var l=t.getRenderList(r).opaque;this._framebuffer.bind(e),e.gl.clearColor(0,0,0,0),e.gl.clear(e.gl.COLOR_BUFFER_BIT|e.gl.DEPTH_BUFFER_BIT),e.gl.disable(e.gl.BLEND),e.renderPass(l,r,{getMaterial:function(){return s},ifRender:function(u){return u.renderNormal},beforeRender:gu(e,this._defaultNormalMap,this._defaultBumpMap,this._defaultRoughessMap,this._normalMaterial),sort:e.opaqueSortCompare}),this._framebuffer.unbind(e)};Zt.prototype.renderDebug=function(e){this._debugPass.render(e)};Zt.prototype.dispose=function(e){this._depthTex.dispose(e),this._normalTex.dispose(e)};function dr(e){e=e||{},this._edgePass=new Me({fragment:z.source("ecgl.edge")}),this._edgePass.setUniform("normalTexture",e.normalTexture),this._edgePass.setUniform("depthTexture",e.depthTexture),this._targetTexture=new K({type:O.HALF_FLOAT}),this._frameBuffer=new me,this._frameBuffer.attach(this._targetTexture)}dr.prototype.update=function(e,t,r,i){var n=e.getWidth(),a=e.getHeight(),o=this._targetTexture;o.width=n,o.height=a;var s=this._frameBuffer;s.bind(e),this._edgePass.setUniform("projectionInv",t.invProjectionMatrix.array),this._edgePass.setUniform("textureSize",[n,a]),this._edgePass.setUniform("texture",r),this._edgePass.render(e),s.unbind(e)};dr.prototype.getTargetTexture=function(){return this._targetTexture};dr.prototype.setParameter=function(e,t){this._edgePass.setUniform(e,t)};dr.prototype.dispose=function(e){this._targetTexture.dispose(e),this._frameBuffer.dispose(e)};const yu={nodes:[{name:"source",type:"texture",outputs:{color:{}}},{name:"source_half",shader:"#source(clay.compositor.downsample)",inputs:{texture:"source"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 2)",height:"expr(height * 1.0 / 2)",type:"HALF_FLOAT"}}},parameters:{textureSize:"expr( [width * 1.0, height * 1.0] )"}},{name:"bright",shader:"#source(clay.compositor.bright)",inputs:{texture:"source_half"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 2)",height:"expr(height * 1.0 / 2)",type:"HALF_FLOAT"}}},parameters:{threshold:2,scale:4,textureSize:"expr([width * 1.0 / 2, height / 2])"}},{name:"bright_downsample_4",shader:"#source(clay.compositor.downsample)",inputs:{texture:"bright"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 4)",height:"expr(height * 1.0 / 4)",type:"HALF_FLOAT"}}},parameters:{textureSize:"expr( [width * 1.0 / 2, height / 2] )"}},{name:"bright_downsample_8",shader:"#source(clay.compositor.downsample)",inputs:{texture:"bright_downsample_4"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 8)",height:"expr(height * 1.0 / 8)",type:"HALF_FLOAT"}}},parameters:{textureSize:"expr( [width * 1.0 / 4, height / 4] )"}},{name:"bright_downsample_16",shader:"#source(clay.compositor.downsample)",inputs:{texture:"bright_downsample_8"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 16)",height:"expr(height * 1.0 / 16)",type:"HALF_FLOAT"}}},parameters:{textureSize:"expr( [width * 1.0 / 8, height / 8] )"}},{name:"bright_downsample_32",shader:"#source(clay.compositor.downsample)",inputs:{texture:"bright_downsample_16"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 32)",height:"expr(height * 1.0 / 32)",type:"HALF_FLOAT"}}},parameters:{textureSize:"expr( [width * 1.0 / 16, height / 16] )"}},{name:"bright_upsample_16_blur_h",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_downsample_32"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 16)",height:"expr(height * 1.0 / 16)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:0,textureSize:"expr( [width * 1.0 / 32, height / 32] )"}},{name:"bright_upsample_16_blur_v",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_upsample_16_blur_h"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 16)",height:"expr(height * 1.0 / 16)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:1,textureSize:"expr( [width * 1.0 / 16, height * 1.0 / 16] )"}},{name:"bright_upsample_8_blur_h",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_downsample_16"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 8)",height:"expr(height * 1.0 / 8)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:0,textureSize:"expr( [width * 1.0 / 16, height * 1.0 / 16] )"}},{name:"bright_upsample_8_blur_v",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_upsample_8_blur_h"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 8)",height:"expr(height * 1.0 / 8)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:1,textureSize:"expr( [width * 1.0 / 8, height * 1.0 / 8] )"}},{name:"bright_upsample_8_blend",shader:"#source(clay.compositor.blend)",inputs:{texture1:"bright_upsample_8_blur_v",texture2:"bright_upsample_16_blur_v"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 8)",height:"expr(height * 1.0 / 8)",type:"HALF_FLOAT"}}},parameters:{weight1:.3,weight2:.7}},{name:"bright_upsample_4_blur_h",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_downsample_8"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 4)",height:"expr(height * 1.0 / 4)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:0,textureSize:"expr( [width * 1.0 / 8, height * 1.0 / 8] )"}},{name:"bright_upsample_4_blur_v",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_upsample_4_blur_h"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 4)",height:"expr(height * 1.0 / 4)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:1,textureSize:"expr( [width * 1.0 / 4, height * 1.0 / 4] )"}},{name:"bright_upsample_4_blend",shader:"#source(clay.compositor.blend)",inputs:{texture1:"bright_upsample_4_blur_v",texture2:"bright_upsample_8_blend"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 4)",height:"expr(height * 1.0 / 4)",type:"HALF_FLOAT"}}},parameters:{weight1:.3,weight2:.7}},{name:"bright_upsample_2_blur_h",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_downsample_4"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 2)",height:"expr(height * 1.0 / 2)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:0,textureSize:"expr( [width * 1.0 / 4, height * 1.0 / 4] )"}},{name:"bright_upsample_2_blur_v",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_upsample_2_blur_h"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 2)",height:"expr(height * 1.0 / 2)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:1,textureSize:"expr( [width * 1.0 / 2, height * 1.0 / 2] )"}},{name:"bright_upsample_2_blend",shader:"#source(clay.compositor.blend)",inputs:{texture1:"bright_upsample_2_blur_v",texture2:"bright_upsample_4_blend"},outputs:{color:{parameters:{width:"expr(width * 1.0 / 2)",height:"expr(height * 1.0 / 2)",type:"HALF_FLOAT"}}},parameters:{weight1:.3,weight2:.7}},{name:"bright_upsample_full_blur_h",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright"},outputs:{color:{parameters:{width:"expr(width * 1.0)",height:"expr(height * 1.0)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:0,textureSize:"expr( [width * 1.0 / 2, height * 1.0 / 2] )"}},{name:"bright_upsample_full_blur_v",shader:"#source(clay.compositor.gaussian_blur)",inputs:{texture:"bright_upsample_full_blur_h"},outputs:{color:{parameters:{width:"expr(width * 1.0)",height:"expr(height * 1.0)",type:"HALF_FLOAT"}}},parameters:{blurSize:1,blurDir:1,textureSize:"expr( [width * 1.0, height * 1.0] )"}},{name:"bloom_composite",shader:"#source(clay.compositor.blend)",inputs:{texture1:"bright_upsample_full_blur_v",texture2:"bright_upsample_2_blend"},outputs:{color:{parameters:{width:"expr(width * 1.0)",height:"expr(height * 1.0)",type:"HALF_FLOAT"}}},parameters:{weight1:.3,weight2:.7}},{name:"coc",shader:"#source(ecgl.dof.coc)",outputs:{color:{parameters:{minFilter:"NEAREST",magFilter:"NEAREST",width:"expr(width * 1.0)",height:"expr(height * 1.0)"}}},parameters:{focalDist:50,focalRange:30}},{name:"dof_far_blur",shader:"#source(ecgl.dof.diskBlur)",inputs:{texture:"source",coc:"coc"},outputs:{color:{parameters:{width:"expr(width * 1.0)",height:"expr(height * 1.0)",type:"HALF_FLOAT"}}},parameters:{textureSize:"expr( [width * 1.0, height * 1.0] )"}},{name:"dof_near_blur",shader:"#source(ecgl.dof.diskBlur)",inputs:{texture:"source",coc:"coc"},outputs:{color:{parameters:{width:"expr(width * 1.0)",height:"expr(height * 1.0)",type:"HALF_FLOAT"}}},parameters:{textureSize:"expr( [width * 1.0, height * 1.0] )"},defines:{BLUR_NEARFIELD:null}},{name:"dof_coc_blur",shader:"#source(ecgl.dof.diskBlur)",inputs:{texture:"coc"},outputs:{color:{parameters:{minFilter:"NEAREST",magFilter:"NEAREST",width:"expr(width * 1.0)",height:"expr(height * 1.0)"}}},parameters:{textureSize:"expr( [width * 1.0, height * 1.0] )"},defines:{BLUR_COC:null}},{name:"dof_composite",shader:"#source(ecgl.dof.composite)",inputs:{original:"source",blurred:"dof_far_blur",nearfield:"dof_near_blur",coc:"coc",nearcoc:"dof_coc_blur"},outputs:{color:{parameters:{width:"expr(width * 1.0)",height:"expr(height * 1.0)",type:"HALF_FLOAT"}}}},{name:"composite",shader:"#source(clay.compositor.hdr.composite)",inputs:{texture:"source",bloom:"bloom_composite"},outputs:{color:{parameters:{width:"expr(width * 1.0)",height:"expr(height * 1.0)"}}},defines:{}},{name:"FXAA",shader:"#source(clay.compositor.fxaa)",inputs:{texture:"composite"}}]},xu=`@export ecgl.dof.coc

uniform sampler2D depth;

uniform float zNear: 0.1;
uniform float zFar: 2000;

uniform float focalDistance: 3;
uniform float focalRange: 1;
uniform float focalLength: 30;
uniform float fstop: 2.8;

varying vec2 v_Texcoord;

@import clay.util.encode_float

void main()
{
 float z = texture2D(depth, v_Texcoord).r * 2.0 - 1.0;

 float dist = 2.0 * zNear * zFar / (zFar + zNear - z * (zFar - zNear));

 float aperture = focalLength / fstop;

 float coc;

 float uppper = focalDistance + focalRange;
 float lower = focalDistance - focalRange;
 if (dist <= uppper && dist >= lower) {
 coc = 0.5;
 }
 else {
 float focalAdjusted = dist > uppper ? uppper : lower;

 coc = abs(aperture * (focalLength * (dist - focalAdjusted)) / (dist * (focalAdjusted - focalLength)));
 coc = clamp(coc, 0.0, 2.0) / 2.00001;

 if (dist < lower) {
 coc = -coc;
 }
 coc = coc * 0.5 + 0.5;
 }

 gl_FragColor = encodeFloat(coc);
}
@end


@export ecgl.dof.composite

#define DEBUG 0

uniform sampler2D original;
uniform sampler2D blurred;
uniform sampler2D nearfield;
uniform sampler2D coc;
uniform sampler2D nearcoc;
varying vec2 v_Texcoord;

@import clay.util.rgbm
@import clay.util.float

void main()
{
 vec4 blurredColor = texture2D(blurred, v_Texcoord);
 vec4 originalColor = texture2D(original, v_Texcoord);

 float fCoc = decodeFloat(texture2D(coc, v_Texcoord));

 fCoc = abs(fCoc * 2.0 - 1.0);

 float weight = smoothstep(0.0, 1.0, fCoc);
 
#ifdef NEARFIELD_ENABLED
 vec4 nearfieldColor = texture2D(nearfield, v_Texcoord);
 float fNearCoc = decodeFloat(texture2D(nearcoc, v_Texcoord));
 fNearCoc = abs(fNearCoc * 2.0 - 1.0);

 gl_FragColor = encodeHDR(
 mix(
 nearfieldColor, mix(originalColor, blurredColor, weight),
 pow(1.0 - fNearCoc, 4.0)
 )
 );
#else
 gl_FragColor = encodeHDR(mix(originalColor, blurredColor, weight));
#endif

}

@end



@export ecgl.dof.diskBlur

#define POISSON_KERNEL_SIZE 16;

uniform sampler2D texture;
uniform sampler2D coc;
varying vec2 v_Texcoord;

uniform float blurRadius : 10.0;
uniform vec2 textureSize : [512.0, 512.0];

uniform vec2 poissonKernel[POISSON_KERNEL_SIZE];

uniform float percent;

float nrand(const in vec2 n) {
 return fract(sin(dot(n.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

@import clay.util.rgbm
@import clay.util.float


void main()
{
 vec2 offset = blurRadius / textureSize;

 float rnd = 6.28318 * nrand(v_Texcoord + 0.07 * percent );
 float cosa = cos(rnd);
 float sina = sin(rnd);
 vec4 basis = vec4(cosa, -sina, sina, cosa);

#if !defined(BLUR_NEARFIELD) && !defined(BLUR_COC)
 offset *= abs(decodeFloat(texture2D(coc, v_Texcoord)) * 2.0 - 1.0);
#endif

#ifdef BLUR_COC
 float cocSum = 0.0;
#else
 vec4 color = vec4(0.0);
#endif


 float weightSum = 0.0;

 for (int i = 0; i < POISSON_KERNEL_SIZE; i++) {
 vec2 ofs = poissonKernel[i];

 ofs = vec2(dot(ofs, basis.xy), dot(ofs, basis.zw));

 vec2 uv = v_Texcoord + ofs * offset;
 vec4 texel = texture2D(texture, uv);

 float w = 1.0;
#ifdef BLUR_COC
 float fCoc = decodeFloat(texel) * 2.0 - 1.0;
 cocSum += clamp(fCoc, -1.0, 0.0) * w;
#else
 texel = texel;
 #if !defined(BLUR_NEARFIELD)
 float fCoc = decodeFloat(texture2D(coc, uv)) * 2.0 - 1.0;
 w *= abs(fCoc);
 #endif
 texel.rgb *= texel.a;
 color += texel * w;
#endif

 weightSum += w;
 }

#ifdef BLUR_COC
 gl_FragColor = encodeFloat(clamp(cocSum / weightSum, -1.0, 0.0) * 0.5 + 0.5);
#else
 color /= weightSum;
 color.rgb /= (color.a + 0.0001);
 gl_FragColor = color;
#endif
}

@end`,Tu=`@export ecgl.edge

uniform sampler2D texture;

uniform sampler2D normalTexture;
uniform sampler2D depthTexture;

uniform mat4 projectionInv;

uniform vec2 textureSize;

uniform vec4 edgeColor: [0,0,0,0.8];

varying vec2 v_Texcoord;

vec3 packColor(vec2 coord) {
 float z = texture2D(depthTexture, coord).r * 2.0 - 1.0;
 vec4 p = vec4(v_Texcoord * 2.0 - 1.0, z, 1.0);
 vec4 p4 = projectionInv * p;

 return vec3(
 texture2D(normalTexture, coord).rg,
 -p4.z / p4.w / 5.0
 );
}

void main() {
 vec2 cc = v_Texcoord;
 vec3 center = packColor(cc);

 float size = clamp(1.0 - (center.z - 10.0) / 100.0, 0.0, 1.0) * 0.5;
 float dx = size / textureSize.x;
 float dy = size / textureSize.y;

 vec2 coord;
 vec3 topLeft = packColor(cc+vec2(-dx, -dy));
 vec3 top = packColor(cc+vec2(0.0, -dy));
 vec3 topRight = packColor(cc+vec2(dx, -dy));
 vec3 left = packColor(cc+vec2(-dx, 0.0));
 vec3 right = packColor(cc+vec2(dx, 0.0));
 vec3 bottomLeft = packColor(cc+vec2(-dx, dy));
 vec3 bottom = packColor(cc+vec2(0.0, dy));
 vec3 bottomRight = packColor(cc+vec2(dx, dy));

 vec3 v = -topLeft-2.0*top-topRight+bottomLeft+2.0*bottom+bottomRight;
 vec3 h = -bottomLeft-2.0*left-topLeft+bottomRight+2.0*right+topRight;

 float edge = sqrt(dot(h, h) + dot(v, v));

 edge = smoothstep(0.8, 1.0, edge);

 gl_FragColor = mix(texture2D(texture, v_Texcoord), vec4(edgeColor.rgb, 1.0), edgeColor.a * edge);
}
@end`;z.import(Da);z.import(Pa);z.import(Na);z.import(Ra);z.import(Oa);z.import(Ia);z.import(Ba);z.import(Fa);z.import(Ua);z.import(xu);z.import(Tu);function Va(e,t){return{color:{parameters:{width:e,height:t}}}}var Hi=["composite","FXAA"];function j(){this._width,this._height,this._dpr,this._sourceTexture=new K({type:O.HALF_FLOAT}),this._depthTexture=new K({format:O.DEPTH_COMPONENT,type:O.UNSIGNED_INT}),this._framebuffer=new me,this._framebuffer.attach(this._sourceTexture),this._framebuffer.attach(this._depthTexture,me.DEPTH_ATTACHMENT),this._normalPass=new Zt,this._compositor=su(yu);var e=this._compositor.getNodeByName("source");e.texture=this._sourceTexture;var t=this._compositor.getNodeByName("coc");this._sourceNode=e,this._cocNode=t,this._compositeNode=this._compositor.getNodeByName("composite"),this._fxaaNode=this._compositor.getNodeByName("FXAA"),this._dofBlurNodes=["dof_far_blur","dof_near_blur","dof_coc_blur"].map(function(i){return this._compositor.getNodeByName(i)},this),this._dofBlurKernel=0,this._dofBlurKernelSize=new Float32Array(0),this._finalNodesChain=Hi.map(function(i){return this._compositor.getNodeByName(i)},this);var r={normalTexture:this._normalPass.getNormalTexture(),depthTexture:this._normalPass.getDepthTexture()};this._ssaoPass=new ot(r),this._ssrPass=new st(r),this._edgePass=new dr(r)}j.prototype.resize=function(i,n,r){r=r||1;var i=i*r,n=n*r,a=this._sourceTexture,o=this._depthTexture;a.width=i,a.height=n,o.width=i,o.height=n;var s={getWidth:function(){return i},getHeight:function(){return n},getDevicePixelRatio:function(){return r}};function l(u,f){if(typeof u[f]=="function"){var h=u[f].__original||u[f];u[f]=function(d){return h.call(this,s)},u[f].__original=h}}this._compositor.nodes.forEach(function(u){for(var f in u.outputs){var h=u.outputs[f].parameters;h&&(l(h,"width"),l(h,"height"))}for(var d in u.parameters)l(u.parameters,d)}),this._width=i,this._height=n,this._dpr=r};j.prototype.getWidth=function(){return this._width};j.prototype.getHeight=function(){return this._height};j.prototype._ifRenderNormalPass=function(){return this._enableSSAO||this._enableEdge||this._enableSSR};j.prototype._getPrevNode=function(e){for(var t=Hi.indexOf(e.name)-1,r=this._finalNodesChain[t];r&&!this._compositor.getNodeByName(r.name);)t-=1,r=this._finalNodesChain[t];return r};j.prototype._getNextNode=function(e){for(var t=Hi.indexOf(e.name)+1,r=this._finalNodesChain[t];r&&!this._compositor.getNodeByName(r.name);)t+=1,r=this._finalNodesChain[t];return r};j.prototype._addChainNode=function(e){var t=this._getPrevNode(e),r=this._getNextNode(e);t&&(e.inputs.texture=t.name,r?(e.outputs=Va(this.getWidth.bind(this),this.getHeight.bind(this)),r.inputs.texture=e.name):e.outputs=null,this._compositor.addNode(e))};j.prototype._removeChainNode=function(e){var t=this._getPrevNode(e),r=this._getNextNode(e);t&&(r?(t.outputs=Va(this.getWidth.bind(this),this.getHeight.bind(this)),r.inputs.texture=t.name):t.outputs=null,this._compositor.removeNode(e))};j.prototype.updateNormal=function(e,t,r,i){this._ifRenderNormalPass()&&this._normalPass.update(e,t,r)};j.prototype.updateSSAO=function(e,t,r,i){this._ssaoPass.update(e,r,i)};j.prototype.enableSSAO=function(){this._enableSSAO=!0};j.prototype.disableSSAO=function(){this._enableSSAO=!1};j.prototype.enableSSR=function(){this._enableSSR=!0};j.prototype.disableSSR=function(){this._enableSSR=!1};j.prototype.getSSAOTexture=function(){return this._ssaoPass.getTargetTexture()};j.prototype.getSourceFrameBuffer=function(){return this._framebuffer};j.prototype.getSourceTexture=function(){return this._sourceTexture};j.prototype.disableFXAA=function(){this._removeChainNode(this._fxaaNode)};j.prototype.enableFXAA=function(){this._addChainNode(this._fxaaNode)};j.prototype.enableBloom=function(){this._compositeNode.inputs.bloom="bloom_composite",this._compositor.dirty()};j.prototype.disableBloom=function(){this._compositeNode.inputs.bloom=null,this._compositor.dirty()};j.prototype.enableDOF=function(){this._compositeNode.inputs.texture="dof_composite",this._compositor.dirty()};j.prototype.disableDOF=function(){this._compositeNode.inputs.texture="source",this._compositor.dirty()};j.prototype.enableColorCorrection=function(){this._compositeNode.define("COLOR_CORRECTION"),this._enableColorCorrection=!0};j.prototype.disableColorCorrection=function(){this._compositeNode.undefine("COLOR_CORRECTION"),this._enableColorCorrection=!1};j.prototype.enableEdge=function(){this._enableEdge=!0};j.prototype.disableEdge=function(){this._enableEdge=!1};j.prototype.setBloomIntensity=function(e){this._compositeNode.setParameter("bloomIntensity",e)};j.prototype.setSSAOParameter=function(e,t){switch(e){case"quality":var r={low:6,medium:12,high:32,ultra:62}[t]||12;this._ssaoPass.setParameter("kernelSize",r);break;case"radius":this._ssaoPass.setParameter(e,t),this._ssaoPass.setParameter("bias",t/200);break;case"intensity":this._ssaoPass.setParameter(e,t);break}};j.prototype.setDOFParameter=function(e,t){switch(e){case"focalDistance":case"focalRange":case"fstop":this._cocNode.setParameter(e,t);break;case"blurRadius":for(var r=0;r<this._dofBlurNodes.length;r++)this._dofBlurNodes[r].setParameter("blurRadius",t);break;case"quality":var i={low:4,medium:8,high:16,ultra:32}[t]||8;this._dofBlurKernelSize=i;for(var r=0;r<this._dofBlurNodes.length;r++)this._dofBlurNodes[r].pass.material.define("POISSON_KERNEL_SIZE",i);this._dofBlurKernel=new Float32Array(i*2);break}};j.prototype.setSSRParameter=function(e,t){if(t!=null)switch(e){case"quality":var r={low:10,medium:15,high:30,ultra:80}[t]||20,i={low:32,medium:16,high:8,ultra:4}[t]||16;this._ssrPass.setParameter("maxIteration",r),this._ssrPass.setParameter("pixelStride",i);break;case"maxRoughness":this._ssrPass.setParameter("minGlossiness",Math.max(Math.min(1-t,1),0));break;case"physical":this.setPhysicallyCorrectSSR(t);break;default:console.warn("Unkown SSR parameter "+e)}};j.prototype.setPhysicallyCorrectSSR=function(e){this._ssrPass.setPhysicallyCorrect(e)};j.prototype.setEdgeColor=function(e){var t=w.parseColor(e);this._edgePass.setParameter("edgeColor",t)};j.prototype.setExposure=function(e){this._compositeNode.setParameter("exposure",Math.pow(2,e))};j.prototype.setColorLookupTexture=function(e,t){this._compositeNode.pass.material.setTextureImage("lut",this._enableColorCorrection?e:"none",t,{minFilter:w.Texture.NEAREST,magFilter:w.Texture.NEAREST,flipY:!1})};j.prototype.setColorCorrection=function(e,t){this._compositeNode.setParameter(e,t)};j.prototype.isSSREnabled=function(){return this._enableSSR};j.prototype.composite=function(e,t,r,i,n){var a=this._sourceTexture,o=a;this._enableEdge&&(this._edgePass.update(e,r,a,n),a=o=this._edgePass.getTargetTexture()),this._enableSSR&&(this._ssrPass.update(e,r,a,n),o=this._ssrPass.getTargetTexture(),this._ssrPass.setSSAOTexture(this._enableSSAO?this._ssaoPass.getTargetTexture():null)),this._sourceNode.texture=o,this._cocNode.setParameter("depth",this._depthTexture);for(var s=this._dofBlurKernel,l=this._dofBlurKernelSize,u=Math.floor(Wn.length/2/l),f=n%u,h=0;h<l*2;h++)s[h]=Wn[h+f*l*2];for(var h=0;h<this._dofBlurNodes.length;h++)this._dofBlurNodes[h].setParameter("percent",n/30),this._dofBlurNodes[h].setParameter("poissonKernel",s);this._cocNode.setParameter("zNear",r.near),this._cocNode.setParameter("zFar",r.far),this._compositor.render(e,i)};j.prototype.dispose=function(e){this._sourceTexture.dispose(e),this._depthTexture.dispose(e),this._framebuffer.dispose(e),this._compositor.dispose(e),this._normalPass.dispose(e),this._ssaoPass.dispose(e)};function wi(e){for(var t=[],r=0;r<30;r++)t.push([Xt(r,2),Xt(r,3)]);this._haltonSequence=t,this._frame=0,this._sourceTex=new K,this._sourceFb=new me,this._sourceFb.attach(this._sourceTex),this._prevFrameTex=new K,this._outputTex=new K;var i=this._blendPass=new Me({fragment:z.source("clay.compositor.blend")});i.material.disableTexturesAll(),i.material.enableTexture(["texture1","texture2"]),this._blendFb=new me({depthBuffer:!1}),this._outputPass=new Me({fragment:z.source("clay.compositor.output"),blendWithPrevious:!0}),this._outputPass.material.define("fragment","OUTPUT_ALPHA"),this._outputPass.material.blend=function(n){n.blendEquationSeparate(n.FUNC_ADD,n.FUNC_ADD),n.blendFuncSeparate(n.ONE,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA)}}wi.prototype={constructor:wi,jitterProjection:function(e,t){var r=e.viewport,i=r.devicePixelRatio||e.getDevicePixelRatio(),n=r.width*i,a=r.height*i,o=this._haltonSequence[this._frame%this._haltonSequence.length],s=new F;s.array[12]=(o[0]*2-1)/n,s.array[13]=(o[1]*2-1)/a,F.mul(t.projectionMatrix,s,t.projectionMatrix),F.invert(t.invProjectionMatrix,t.projectionMatrix)},resetFrame:function(){this._frame=0},getFrame:function(){return this._frame},getSourceFrameBuffer:function(){return this._sourceFb},getOutputTexture:function(){return this._outputTex},resize:function(e,t){this._prevFrameTex.width=e,this._prevFrameTex.height=t,this._outputTex.width=e,this._outputTex.height=t,this._sourceTex.width=e,this._sourceTex.height=t,this._prevFrameTex.dirty(),this._outputTex.dirty(),this._sourceTex.dirty()},isFinished:function(){return this._frame>=this._haltonSequence.length},render:function(e,t,r){var i=this._blendPass;this._frame===0?(i.setUniform("weight1",0),i.setUniform("weight2",1)):(i.setUniform("weight1",.9),i.setUniform("weight2",.1)),i.setUniform("texture1",this._prevFrameTex),i.setUniform("texture2",t||this._sourceTex),this._blendFb.attach(this._outputTex),this._blendFb.bind(e),i.render(e),this._blendFb.unbind(e),r||(this._outputPass.setUniform("texture",this._outputTex),this._outputPass.render(e));var n=this._prevFrameTex;this._prevFrameTex=this._outputTex,this._outputTex=n,this._frame++},dispose:function(e){this._sourceFb.dispose(e),this._blendFb.dispose(e),this._prevFrameTex.dispose(e),this._outputTex.dispose(e),this._sourceTex.dispose(e),this._outputPass.dispose(e),this._blendPass.dispose(e)}};function se(e){e=e||"perspective",this.layer=null,this.scene=new vt,this.rootNode=this.scene,this.viewport={x:0,y:0,width:0,height:0},this.setProjection(e),this._compositor=new j,this._temporalSS=new wi,this._shadowMapPass=new Ze;for(var t=[],r=0,i=0;i<30;i++){for(var n=[],a=0;a<6;a++)n.push(Xt(r,2)*4-2),n.push(Xt(r,3)*4-2),r++;t.push(n)}this._pcfKernels=t,this.scene.on("beforerender",function(o,s,l){this.needsTemporalSS()&&this._temporalSS.jitterProjection(o,l)},this)}se.prototype.setProjection=function(e){var t=this.camera;t&&t.update(),e==="perspective"?this.camera instanceof ge||(this.camera=new ge,t&&this.camera.setLocalTransform(t.localTransform)):this.camera instanceof ur||(this.camera=new ur,t&&this.camera.setLocalTransform(t.localTransform)),this.camera.near=.1,this.camera.far=2e3};se.prototype.setViewport=function(e,t,r,i,n){this.camera instanceof ge&&(this.camera.aspect=r/i),n=n||1,this.viewport.x=e,this.viewport.y=t,this.viewport.width=r,this.viewport.height=i,this.viewport.devicePixelRatio=n,this._compositor.resize(r*n,i*n),this._temporalSS.resize(r*n,i*n)};se.prototype.containPoint=function(e,t){var r=this.viewport,i=this.layer.renderer.getHeight();return t=i-t,e>=r.x&&t>=r.y&&e<=r.x+r.width&&t<=r.y+r.height};var Xn=new W;se.prototype.castRay=function(e,t,r){var i=this.layer.renderer,n=i.viewport;return i.viewport=this.viewport,i.screenToNDC(e,t,Xn),this.camera.castRay(Xn,r),i.viewport=n,r};se.prototype.prepareRender=function(){this.scene.update(),this.camera.update(),this.scene.updateLights();var e=this.scene.updateRenderList(this.camera);this._needsSortProgressively=!1;for(var t=0;t<e.transparent.length;t++){var r=e.transparent[t],i=r.geometry;i.needsSortVerticesProgressively&&i.needsSortVerticesProgressively()&&(this._needsSortProgressively=!0),i.needsSortTrianglesProgressively&&i.needsSortTrianglesProgressively()&&(this._needsSortProgressively=!0)}this._frame=0,this._temporalSS.resetFrame()};se.prototype.render=function(e,t){this._doRender(e,t,this._frame),this._frame++};se.prototype.needsAccumulate=function(){return this.needsTemporalSS()||this._needsSortProgressively};se.prototype.needsTemporalSS=function(){var e=this._enableTemporalSS;return e==="auto"&&(e=this._enablePostEffect),e};se.prototype.hasDOF=function(){return this._enableDOF};se.prototype.isAccumulateFinished=function(){return this.needsTemporalSS()?this._temporalSS.isFinished():this._frame>30};se.prototype._doRender=function(e,t,r){var i=this.scene,n=this.camera;r=r||0,this._updateTransparent(e,i,n,r),t||(this._shadowMapPass.kernelPCF=this._pcfKernels[0],this._shadowMapPass.render(e,i,n,!0)),this._updateShadowPCFKernel(r);var a=e.clearColor;if(e.gl.clearColor(a[0],a[1],a[2],a[3]),this._enablePostEffect&&(this.needsTemporalSS()&&this._temporalSS.jitterProjection(e,n),this._compositor.updateNormal(e,i,n,this._temporalSS.getFrame())),this._updateSSAO(e,i,n,this._temporalSS.getFrame()),this._enablePostEffect){var o=this._compositor.getSourceFrameBuffer();o.bind(e),e.gl.clear(e.gl.DEPTH_BUFFER_BIT|e.gl.COLOR_BUFFER_BIT),e.render(i,n,!0,!0),o.unbind(e),this.needsTemporalSS()&&t?(this._compositor.composite(e,i,n,this._temporalSS.getSourceFrameBuffer(),this._temporalSS.getFrame()),e.setViewport(this.viewport),this._temporalSS.render(e)):(e.setViewport(this.viewport),this._compositor.composite(e,i,n,null,0))}else if(this.needsTemporalSS()&&t){var o=this._temporalSS.getSourceFrameBuffer();o.bind(e),e.saveClear(),e.clearBit=e.gl.DEPTH_BUFFER_BIT|e.gl.COLOR_BUFFER_BIT,e.render(i,n,!0,!0),e.restoreClear(),o.unbind(e),e.setViewport(this.viewport),this._temporalSS.render(e)}else e.setViewport(this.viewport),e.render(i,n,!0,!0)};se.prototype._updateTransparent=function(e,t,r,i){for(var n=new b,a=new F,o=r.getWorldPosition(),s=t.getRenderList(r).transparent,l=0;l<s.length;l++){var u=s[l],f=u.geometry;F.invert(a,u.worldTransform),b.transformMat4(n,o,a),f.needsSortTriangles&&f.needsSortTriangles()&&f.doSortTriangles(n,i),f.needsSortVertices&&f.needsSortVertices()&&f.doSortVertices(n,i)}};se.prototype._updateSSAO=function(e,t,r){var i=this._enableSSAO&&this._enablePostEffect;i&&this._compositor.updateSSAO(e,t,r,this._temporalSS.getFrame());for(var n=t.getRenderList(r),a=0;a<n.opaque.length;a++){var o=n.opaque[a];o.renderNormal&&o.material[i?"enableTexture":"disableTexture"]("ssaoMap"),i&&o.material.set("ssaoMap",this._compositor.getSSAOTexture())}};se.prototype._updateShadowPCFKernel=function(e){for(var t=this._pcfKernels[e%this._pcfKernels.length],r=this.scene.getRenderList(this.camera),i=r.opaque,n=0;n<i.length;n++)i[n].receiveShadow&&(i[n].material.set("pcfKernel",t),i[n].material.define("fragment","PCF_KERNEL_SIZE",t.length/2))};se.prototype.dispose=function(e){this._compositor.dispose(e.gl),this._temporalSS.dispose(e.gl),this._shadowMapPass.dispose(e)};se.prototype.setPostEffect=function(e,t){var r=this._compositor;this._enablePostEffect=e.get("enable");var i=e.getModel("bloom"),n=e.getModel("edge"),a=e.getModel("DOF",e.getModel("depthOfField")),o=e.getModel("SSAO",e.getModel("screenSpaceAmbientOcclusion")),s=e.getModel("SSR",e.getModel("screenSpaceReflection")),l=e.getModel("FXAA"),u=e.getModel("colorCorrection");i.get("enable")?r.enableBloom():r.disableBloom(),a.get("enable")?r.enableDOF():r.disableDOF(),s.get("enable")?r.enableSSR():r.disableSSR(),u.get("enable")?r.enableColorCorrection():r.disableColorCorrection(),n.get("enable")?r.enableEdge():r.disableEdge(),l.get("enable")?r.enableFXAA():r.disableFXAA(),this._enableDOF=a.get("enable"),this._enableSSAO=o.get("enable"),this._enableSSAO?r.enableSSAO():r.disableSSAO(),r.setBloomIntensity(i.get("intensity")),r.setEdgeColor(n.get("color")),r.setColorLookupTexture(u.get("lookupTexture"),t),r.setExposure(u.get("exposure")),["radius","quality","intensity"].forEach(function(f){r.setSSAOParameter(f,o.get(f))}),["quality","maxRoughness","physical"].forEach(function(f){r.setSSRParameter(f,s.get(f))}),["quality","focalDistance","focalRange","blurRadius","fstop"].forEach(function(f){r.setDOFParameter(f,a.get(f))}),["brightness","contrast","saturation"].forEach(function(f){r.setColorCorrection(f,u.get(f))})};se.prototype.setDOFFocusOnPoint=function(e){if(this._enablePostEffect)return e>this.camera.far||e<this.camera.near?void 0:(this._compositor.setDOFParameter("focalDistance",e),!0)};se.prototype.setTemporalSuperSampling=function(e){this._enableTemporalSS=e.get("enable")};se.prototype.isLinearSpace=function(){return this._enablePostEffect};se.prototype.setRootNode=function(e){if(this.rootNode!==e){for(var t=this.rootNode.children(),r=0;r<t.length;r++)e.add(t[r]);e!==this.scene&&this.scene.add(e),this.rootNode=e}};se.prototype.add=function(e){this.rootNode.add(e)};se.prototype.remove=function(e){this.rootNode.remove(e)};se.prototype.removeAll=function(e){this.rootNode.removeAll(e)};Object.assign(se.prototype,Di);var ir=Ce.firstNotNull,qn={left:0,middle:1,right:2};function jn(e){return e instanceof Array||(e=[e,e]),e}var Ga=be.extend(function(){return{zr:null,viewGL:null,_center:new b,minDistance:.5,maxDistance:1.5,maxOrthographicSize:300,minOrthographicSize:30,minAlpha:-90,maxAlpha:90,minBeta:-1/0,maxBeta:1/0,autoRotateAfterStill:0,autoRotateDirection:"cw",autoRotateSpeed:60,damping:.8,rotateSensitivity:1,zoomSensitivity:1,panSensitivity:1,panMouseButton:"middle",rotateMouseButton:"left",_mode:"rotate",_camera:null,_needsUpdate:!1,_rotating:!1,_phi:0,_theta:0,_mouseX:0,_mouseY:0,_rotateVelocity:new W,_panVelocity:new W,_distance:500,_zoomSpeed:0,_stillTimeout:0,_animators:[]}},function(){["_mouseDownHandler","_mouseWheelHandler","_mouseMoveHandler","_mouseUpHandler","_pinchHandler","_contextMenuHandler","_update"].forEach(function(e){this[e]=this[e].bind(this)},this)},{init:function(){var e=this.zr;e&&(e.on("mousedown",this._mouseDownHandler),e.on("globalout",this._mouseUpHandler),e.on("mousewheel",this._mouseWheelHandler),e.on("pinch",this._pinchHandler),e.animation.on("frame",this._update),e.dom.addEventListener("contextmenu",this._contextMenuHandler))},dispose:function(){var e=this.zr;e&&(e.off("mousedown",this._mouseDownHandler),e.off("mousemove",this._mouseMoveHandler),e.off("mouseup",this._mouseUpHandler),e.off("mousewheel",this._mouseWheelHandler),e.off("pinch",this._pinchHandler),e.off("globalout",this._mouseUpHandler),e.dom.removeEventListener("contextmenu",this._contextMenuHandler),e.animation.off("frame",this._update)),this.stopAllAnimation()},getDistance:function(){return this._distance},setDistance:function(e){this._distance=e,this._needsUpdate=!0},getOrthographicSize:function(){return this._orthoSize},setOrthographicSize:function(e){this._orthoSize=e,this._needsUpdate=!0},getAlpha:function(){return this._theta/Math.PI*180},getBeta:function(){return-this._phi/Math.PI*180},getCenter:function(){return this._center.toArray()},setAlpha:function(e){e=Math.max(Math.min(this.maxAlpha,e),this.minAlpha),this._theta=e/180*Math.PI,this._needsUpdate=!0},setBeta:function(e){e=Math.max(Math.min(this.maxBeta,e),this.minBeta),this._phi=-e/180*Math.PI,this._needsUpdate=!0},setCenter:function(e){this._center.setArray(e)},setViewGL:function(e){this.viewGL=e},getCamera:function(){return this.viewGL.camera},setFromViewControlModel:function(e,t){t=t||{};var r=t.baseDistance||0,i=t.baseOrthoSize||1,n=e.get("projection");n!=="perspective"&&n!=="orthographic"&&n!=="isometric"&&(n="perspective"),this._projection=n,this.viewGL.setProjection(n);var a=e.get("distance")+r,o=e.get("orthographicSize")+i;[["damping",.8],["autoRotate",!1],["autoRotateAfterStill",3],["autoRotateDirection","cw"],["autoRotateSpeed",10],["minDistance",30],["maxDistance",400],["minOrthographicSize",30],["maxOrthographicSize",300],["minAlpha",-90],["maxAlpha",90],["minBeta",-1/0],["maxBeta",1/0],["rotateSensitivity",1],["zoomSensitivity",1],["panSensitivity",1],["panMouseButton","left"],["rotateMouseButton","middle"]].forEach(function(d){this[d[0]]=ir(e.get(d[0]),d[1])},this),this.minDistance+=r,this.maxDistance+=r,this.minOrthographicSize+=i,this.maxOrthographicSize+=i;var s=e.ecModel,l={};["animation","animationDurationUpdate","animationEasingUpdate"].forEach(function(d){l[d]=ir(e.get(d),s&&s.get(d))});var u=ir(t.alpha,e.get("alpha"))||0,f=ir(t.beta,e.get("beta"))||0,h=ir(t.center,e.get("center"))||[0,0,0];l.animation&&l.animationDurationUpdate>0&&this._notFirst?this.animateTo({alpha:u,beta:f,center:h,distance:a,orthographicSize:o,easing:l.animationEasingUpdate,duration:l.animationDurationUpdate}):(this.setDistance(a),this.setAlpha(u),this.setBeta(f),this.setCenter(h),this.setOrthographicSize(o)),this._notFirst=!0,this._validateProperties()},_validateProperties:function(){},animateTo:function(e){var t=this.zr,r=this,i={},n={};return e.distance!=null&&(i.distance=this.getDistance(),n.distance=e.distance),e.orthographicSize!=null&&(i.orthographicSize=this.getOrthographicSize(),n.orthographicSize=e.orthographicSize),e.alpha!=null&&(i.alpha=this.getAlpha(),n.alpha=e.alpha),e.beta!=null&&(i.beta=this.getBeta(),n.beta=e.beta),e.center!=null&&(i.center=this.getCenter(),n.center=e.center),this._addAnimator(t.animation.animate(i).when(e.duration||1e3,n).during(function(){i.alpha!=null&&r.setAlpha(i.alpha),i.beta!=null&&r.setBeta(i.beta),i.distance!=null&&r.setDistance(i.distance),i.center!=null&&r.setCenter(i.center),i.orthographicSize!=null&&r.setOrthographicSize(i.orthographicSize),r._needsUpdate=!0})).start(e.easing||"linear")},stopAllAnimation:function(){for(var e=0;e<this._animators.length;e++)this._animators[e].stop();this._animators.length=0},update:function(){this._needsUpdate=!0,this._update(20)},_isAnimating:function(){return this._animators.length>0},_update:function(e){if(this._rotating){var t=(this.autoRotateDirection==="cw"?1:-1)*this.autoRotateSpeed/180*Math.PI;this._phi-=t*e/1e3,this._needsUpdate=!0}else this._rotateVelocity.len()>0&&(this._needsUpdate=!0);(Math.abs(this._zoomSpeed)>.1||this._panVelocity.len()>0)&&(this._needsUpdate=!0),this._needsUpdate&&(e=Math.min(e,50),this._updateDistanceOrSize(e),this._updatePan(e),this._updateRotate(e),this._updateTransform(),this.getCamera().update(),this.zr&&this.zr.refresh(),this.trigger("update"),this._needsUpdate=!1)},_updateRotate:function(e){var t=this._rotateVelocity;this._phi=t.y*e/20+this._phi,this._theta=t.x*e/20+this._theta,this.setAlpha(this.getAlpha()),this.setBeta(this.getBeta()),this._vectorDamping(t,Math.pow(this.damping,e/16))},_updateDistanceOrSize:function(e){this._projection==="perspective"?this._setDistance(this._distance+this._zoomSpeed*e/20):this._setOrthoSize(this._orthoSize+this._zoomSpeed*e/20),this._zoomSpeed*=Math.pow(this.damping,e/16)},_setDistance:function(e){this._distance=Math.max(Math.min(e,this.maxDistance),this.minDistance)},_setOrthoSize:function(e){this._orthoSize=Math.max(Math.min(e,this.maxOrthographicSize),this.minOrthographicSize);var t=this.getCamera(),r=this._orthoSize,i=r/this.viewGL.viewport.height*this.viewGL.viewport.width;t.left=-i/2,t.right=i/2,t.top=r/2,t.bottom=-r/2},_updatePan:function(e){var t=this._panVelocity,r=this._distance,i=this.getCamera(),n=i.worldTransform.y,a=i.worldTransform.x;this._center.scaleAndAdd(a,-t.x*r/200).scaleAndAdd(n,-t.y*r/200),this._vectorDamping(t,0)},_updateTransform:function(){var e=this.getCamera(),t=new b,r=this._theta+Math.PI/2,i=this._phi+Math.PI/2,n=Math.sin(r);t.x=n*Math.cos(i),t.y=-Math.cos(r),t.z=n*Math.sin(i),e.position.copy(this._center).scaleAndAdd(t,this._distance),e.rotation.identity().rotateY(-this._phi).rotateX(-this._theta)},_startCountingStill:function(){clearTimeout(this._stillTimeout);var e=this.autoRotateAfterStill,t=this;!isNaN(e)&&e>0&&(this._stillTimeout=setTimeout(function(){t._rotating=!0},e*1e3))},_vectorDamping:function(e,t){var r=e.len();r=r*t,r<1e-4&&(r=0),e.normalize().scale(r)},_decomposeTransform:function(){if(this.getCamera()){this.getCamera().updateWorldTransform();var e=this.getCamera().worldTransform.z,t=Math.asin(e.y),r=Math.atan2(e.x,e.z);this._theta=t,this._phi=-r,this.setBeta(this.getBeta()),this.setAlpha(this.getAlpha()),this.getCamera().aspect?this._setDistance(this.getCamera().position.dist(this._center)):this._setOrthoSize(this.getCamera().top-this.getCamera().bottom)}},_mouseDownHandler:function(e){if(!e.target&&!this._isAnimating()){var t=e.offsetX,r=e.offsetY;this.viewGL&&!this.viewGL.containPoint(t,r)||(this.zr.on("mousemove",this._mouseMoveHandler),this.zr.on("mouseup",this._mouseUpHandler),e.event.targetTouches?e.event.targetTouches.length===1&&(this._mode="rotate"):e.event.button===qn[this.rotateMouseButton]?this._mode="rotate":e.event.button===qn[this.panMouseButton]?this._mode="pan":this._mode="",this._rotateVelocity.set(0,0),this._rotating=!1,this.autoRotate&&this._startCountingStill(),this._mouseX=e.offsetX,this._mouseY=e.offsetY)}},_mouseMoveHandler:function(e){if(!(e.target&&e.target.__isGLToZRProxy)&&!this._isAnimating()){var t=jn(this.panSensitivity),r=jn(this.rotateSensitivity);this._mode==="rotate"?(this._rotateVelocity.y=(e.offsetX-this._mouseX)/this.zr.getHeight()*2*r[0],this._rotateVelocity.x=(e.offsetY-this._mouseY)/this.zr.getWidth()*2*r[1]):this._mode==="pan"&&(this._panVelocity.x=(e.offsetX-this._mouseX)/this.zr.getWidth()*t[0]*400,this._panVelocity.y=(-e.offsetY+this._mouseY)/this.zr.getHeight()*t[1]*400),this._mouseX=e.offsetX,this._mouseY=e.offsetY,e.event.preventDefault()}},_mouseWheelHandler:function(e){if(!this._isAnimating()){var t=e.event.wheelDelta||-e.event.detail;this._zoomHandler(e,t)}},_pinchHandler:function(e){this._isAnimating()||(this._zoomHandler(e,e.pinchScale>1?1:-1),this._mode="")},_zoomHandler:function(e,t){if(t!==0){var r=e.offsetX,i=e.offsetY;if(!(this.viewGL&&!this.viewGL.containPoint(r,i))){var n;this._projection==="perspective"?n=Math.max(Math.max(Math.min(this._distance-this.minDistance,this.maxDistance-this._distance))/20,.5):n=Math.max(Math.max(Math.min(this._orthoSize-this.minOrthographicSize,this.maxOrthographicSize-this._orthoSize))/20,.5),this._zoomSpeed=(t>0?-1:1)*n*this.zoomSensitivity,this._rotating=!1,this.autoRotate&&this._mode==="rotate"&&this._startCountingStill(),e.event.preventDefault()}}},_mouseUpHandler:function(){this.zr.off("mousemove",this._mouseMoveHandler),this.zr.off("mouseup",this._mouseUpHandler)},_isRightMouseButtonUsed:function(){return this.rotateMouseButton==="right"||this.panMouseButton==="right"},_contextMenuHandler:function(e){this._isRightMouseButtonUsed()&&e.preventDefault()},_addAnimator:function(e){var t=this._animators;return t.push(e),e.done(function(){var r=t.indexOf(e);r>=0&&t.splice(r,1)}),e}});Object.defineProperty(Ga.prototype,"autoRotate",{get:function(e){return this._autoRotate},set:function(e){this._autoRotate=e,this._rotating=e}});function bi(){}bi.prototype={constructor:bi,setScene:function(e){this._scene=e,this._skybox&&this._skybox.attachScene(this._scene)},initLight:function(e){this._lightRoot=e,this.mainLight=new w.DirectionalLight({shadowBias:.005}),this.ambientLight=new w.AmbientLight,e.add(this.mainLight),e.add(this.ambientLight)},dispose:function(){this._lightRoot&&(this._lightRoot.remove(this.mainLight),this._lightRoot.remove(this.ambientLight))},updateLight:function(e){var t=this.mainLight,r=this.ambientLight,i=e.getModel("light"),n=i.getModel("main"),a=i.getModel("ambient");t.intensity=n.get("intensity"),r.intensity=a.get("intensity"),t.color=w.parseColor(n.get("color")).slice(0,3),r.color=w.parseColor(a.get("color")).slice(0,3);var o=n.get("alpha")||0,s=n.get("beta")||0;t.position.setArray(w.directionFromAlphaBeta(o,s)),t.lookAt(w.Vector3.ZERO),t.castShadow=n.get("shadow"),t.shadowResolution=w.getShadowResolution(n.get("shadowQuality"))},updateAmbientCubemap:function(e,t,r){var i=t.getModel("light.ambientCubemap"),n=i.get("texture");if(n){this._cubemapLightsCache=this._cubemapLightsCache||{};var a=this._cubemapLightsCache[n];if(!a){var o=this;a=this._cubemapLightsCache[n]=w.createAmbientCubemap(i.option,e,r,function(){o._isSkyboxFromAmbientCubemap&&o._skybox.setEnvironmentMap(a.specular.cubemap),r.getZr().refresh()})}this._lightRoot.add(a.diffuse),this._lightRoot.add(a.specular),this._currentCubemapLights=a}else this._currentCubemapLights&&(this._lightRoot.remove(this._currentCubemapLights.diffuse),this._lightRoot.remove(this._currentCubemapLights.specular),this._currentCubemapLights=null)},updateSkybox:function(e,t,r){var i=t.get("environment"),n=this;function a(){return n._skybox=n._skybox||new lr,n._skybox}var o=a();if(i&&i!=="none")if(i==="auto")if(this._isSkyboxFromAmbientCubemap=!0,this._currentCubemapLights){var s=this._currentCubemapLights.specular.cubemap;o.setEnvironmentMap(s),this._scene&&o.attachScene(this._scene),o.material.set("lod",3)}else this._skybox&&this._skybox.detachScene();else if(typeof i=="object"&&i.colorStops||typeof i=="string"&&Yn(i)){this._isSkyboxFromAmbientCubemap=!1;var l=new w.Texture2D({anisotropic:8,flipY:!1});o.setEnvironmentMap(l);var u=l.image=document.createElement("canvas");u.width=u.height=16;var f=u.getContext("2d"),h=new Kn({shape:{x:0,y:0,width:16,height:16},style:{fill:i}});$n(f,h),o.attachScene(this._scene)}else{this._isSkyboxFromAmbientCubemap=!1;var l=w.loadTexture(i,r,{anisotropic:8,flipY:!1});o.setEnvironmentMap(l),o.attachScene(this._scene)}else this._skybox&&this._skybox.detachScene(this._scene),this._skybox=null;var d=t.coordinateSystem;if(this._skybox)if(d&&d.viewGL&&i!=="auto"&&!(i.match&&i.match(/.hdr$/))){var c=d.viewGL.isLinearSpace()?"define":"undefine";this._skybox.material[c]("fragment","SRGB_DECODE")}else this._skybox.material.undefine("fragment","SRGB_DECODE")}};var kr=ea.extend({type:"grid3D",dependencies:["xAxis3D","yAxis3D","zAxis3D"],defaultOption:{show:!0,zlevel:-10,left:0,top:0,width:"100%",height:"100%",environment:"auto",boxWidth:100,boxHeight:100,boxDepth:100,axisPointer:{show:!0,lineStyle:{color:"rgba(0, 0, 0, 0.8)",width:1},label:{show:!0,formatter:null,margin:8,textStyle:{fontSize:14,color:"#fff",backgroundColor:"rgba(0,0,0,0.5)",padding:3,borderRadius:3}}},axisLine:{show:!0,lineStyle:{color:"#333",width:2,type:"solid"}},axisTick:{show:!0,inside:!1,length:3,lineStyle:{width:1}},axisLabel:{show:!0,inside:!1,rotate:0,margin:8,textStyle:{fontSize:12}},splitLine:{show:!0,lineStyle:{color:["#ccc"],width:1,type:"solid"}},splitArea:{show:!1,areaStyle:{color:["rgba(250,250,250,0.3)","rgba(200,200,200,0.3)"]}},light:{main:{alpha:30,beta:40},ambient:{intensity:.4}},viewControl:{alpha:20,beta:40,autoRotate:!1,distance:200,minDistance:40,maxDistance:400}}});it(kr.prototype,Xl);it(kr.prototype,ql);it(kr.prototype,jl);var gt=Fe.vec3,ka=J.extend(function(){return{segmentScale:1,useNativeLine:!0,attributes:{position:new J.Attribute("position","float",3,"POSITION"),normal:new J.Attribute("normal","float",3,"NORMAL"),color:new J.Attribute("color","float",4,"COLOR")}}},{resetOffset:function(){this._vertexOffset=0,this._faceOffset=0},setQuadCount:function(e){var t=this.attributes,r=this.getQuadVertexCount()*e,i=this.getQuadTriangleCount()*e;this.vertexCount!==r&&(t.position.init(r),t.normal.init(r),t.color.init(r)),this.triangleCount!==i&&(this.indices=r>65535?new Uint32Array(i*3):new Uint16Array(i*3))},getQuadVertexCount:function(){return 4},getQuadTriangleCount:function(){return 2},addQuad:(function(){var e=gt.create(),t=gt.create(),r=gt.create(),i=[0,3,1,3,2,1];return function(n,a){var o=this.attributes.position,s=this.attributes.normal,l=this.attributes.color;gt.sub(e,n[1],n[0]),gt.sub(t,n[2],n[1]),gt.cross(r,e,t),gt.normalize(r,r);for(var u=0;u<4;u++)o.set(this._vertexOffset+u,n[u]),l.set(this._vertexOffset+u,a),s.set(this._vertexOffset+u,r);for(var f=this._faceOffset*3,u=0;u<6;u++)this.indices[f+u]=i[u]+this._vertexOffset;this._vertexOffset+=4,this._faceOffset+=2}})()});Ct(ka.prototype,Gr);var Ai=Ce.firstNotNull,Eu={x:0,y:2,z:1};function Su(e,t,r,i){var n=[0,0,0],a=i<0?r.getExtentMin():r.getExtentMax();n[Eu[r.dim]]=a,e.position.setArray(n),e.rotation.identity(),t.distance=-Math.abs(a),t.normal.set(0,0,0),r.dim==="x"?(e.rotation.rotateY(i*Math.PI/2),t.normal.x=-i):r.dim==="z"?(e.rotation.rotateX(-i*Math.PI/2),t.normal.y=-i):(i>0&&e.rotation.rotateY(Math.PI),t.normal.z=-i)}function Wr(e,t,r){this.rootNode=new w.Node;var i=new w.Mesh({geometry:new jt({useNativeLine:!1}),material:t,castShadow:!1,ignorePicking:!0,$ignorePicking:!0,renderOrder:1}),n=new w.Mesh({geometry:new ka,material:r,castShadow:!1,culling:!1,ignorePicking:!0,$ignorePicking:!0,renderOrder:0});this.rootNode.add(n),this.rootNode.add(i),this.faceInfo=e,this.plane=new w.Plane,this.linesMesh=i,this.quadsMesh=n}Wr.prototype.update=function(e,t,r){var i=e.coordinateSystem,n=[i.getAxis(this.faceInfo[0]),i.getAxis(this.faceInfo[1])],a=this.linesMesh.geometry,o=this.quadsMesh.geometry;a.convertToDynamicArray(!0),o.convertToDynamicArray(!0),this._updateSplitLines(a,n,e,r),this._udpateSplitAreas(o,n,e,r),a.convertToTypedArray(),o.convertToTypedArray();var s=i.getAxis(this.faceInfo[2]);Su(this.rootNode,this.plane,s,this.faceInfo[3])};Wr.prototype._updateSplitLines=function(e,t,r,i){var n=i.getDevicePixelRatio();t.forEach(function(a,o){var s=a.model,l=t[1-o].getExtent();if(!a.scale.isBlank()){var u=s.getModel("splitLine",r.getModel("splitLine"));if(u.get("show")){var f=u.getModel("lineStyle"),h=f.get("color"),d=Ai(f.get("opacity"),1),c=Ai(f.get("width"),1);h=$e(h)?h:[h];for(var v=a.getTicksCoords({tickModel:u}),p=0,m=0;m<v.length;m++){var _=v[m].coord,x=w.parseColor(h[p%h.length]);x[3]*=d;var T=[0,0,0],g=[0,0,0];T[o]=g[o]=_,T[1-o]=l[0],g[1-o]=l[1],e.addLine(T,g,x,c*n),p++}}}})};Wr.prototype._udpateSplitAreas=function(e,t,r,i){t.forEach(function(n,a){var o=n.model,s=t[1-a].getExtent();if(!n.scale.isBlank()){var l=o.getModel("splitArea",r.getModel("splitArea"));if(l.get("show")){var u=l.getModel("areaStyle"),f=u.get("color"),h=Ai(u.get("opacity"),1);f=$e(f)?f:[f];for(var d=n.getTicksCoords({tickModel:l,clamp:!0}),c=0,v=[0,0,0],p=[0,0,0],m=0;m<d.length;m++){var _=d[m].coord,x=[0,0,0],T=[0,0,0];if(x[a]=T[a]=_,x[1-a]=s[0],T[1-a]=s[1],m===0){v=x,p=T;continue}var g=w.parseColor(f[c%f.length]);g[3]*=h,e.addQuad([v,x,T,p],g),v=x,p=T,c++}}}})};var yt=Ce.firstNotNull,xt={x:0,y:2,z:1};function Vi(e,t){var r=new w.Mesh({geometry:new jt({useNativeLine:!1}),material:t,castShadow:!1,ignorePicking:!0,renderOrder:2}),i=new Ui;i.material.depthMask=!1;var n=new w.Node;n.add(r),n.add(i),this.rootNode=n,this.dim=e,this.linesMesh=r,this.labelsMesh=i,this.axisLineCoords=null,this.labelElements=[]}var _i={x:"y",y:"x",z:"y"};Vi.prototype.update=function(e,t,r){var i=e.coordinateSystem,n=i.getAxis(this.dim),a=this.linesMesh.geometry,o=this.labelsMesh.geometry;a.convertToDynamicArray(!0),o.convertToDynamicArray(!0);var s=n.model,l=n.getExtent(),R=r.getDevicePixelRatio(),u=s.getModel("axisLine",e.getModel("axisLine")),f=s.getModel("axisTick",e.getModel("axisTick")),h=s.getModel("axisLabel",e.getModel("axisLabel")),d=u.get("lineStyle.color");if(u.get("show")){var c=u.getModel("lineStyle"),v=[0,0,0],p=[0,0,0],m=xt[n.dim];v[m]=l[0],p[m]=l[1],this.axisLineCoords=[v,p];var _=w.parseColor(d),x=yt(c.get("width"),1),T=yt(c.get("opacity"),1);_[3]*=T,a.addLine(v,p,_,x*R)}if(f.get("show")){var g=f.getModel("lineStyle"),E=w.parseColor(yt(g.get("color"),d)),x=yt(g.get("width"),1);E[3]*=yt(g.get("opacity"),1);for(var S=n.getTicksCoords(),C=f.get("length"),A=0;A<S.length;A++){var N=S[A].coord,v=[0,0,0],p=[0,0,0],m=xt[n.dim],H=xt[_i[n.dim]];v[m]=p[m]=N,p[H]=C,a.addLine(v,p,E,x*R)}}this.labelElements=[];var R=r.getDevicePixelRatio();if(h.get("show"))for(var S=n.getTicksCoords(),U=s.get("data"),V=h.get("margin"),I=n.getViewLabels(),A=0;A<I.length;A++){var G=I[A].tickValue,X=I[A].formattedLabel,q=I[A].rawLabel,N=n.dataToCoord(G),ie=[0,0,0],m=xt[n.dim],H=xt[_i[n.dim]];ie[m]=ie[m]=N,ie[H]=V;var _e=h;U&&U[G]&&U[G].textStyle&&(_e=new fo(U[G].textStyle,h,s.ecModel));var we=yt(_e.get("color"),d),ce=new Mr({style:Dr(_e,{text:X,fill:typeof we=="function"?we(n.type==="category"?q:n.type==="value"?G+"":G,A):we,verticalAlign:"top",align:"left"})}),xe=t.add(ce),de=ce.getBoundingRect();o.addSprite(ie,[de.width*R,de.height*R],xe),this.labelElements.push(ce)}if(s.get("name")){var Ae=s.getModel("nameTextStyle"),ie=[0,0,0],m=xt[n.dim],H=xt[_i[n.dim]],Be=yt(Ae.get("color"),d),Oe=Ae.get("borderColor"),x=Ae.get("borderWidth");ie[m]=ie[m]=(l[0]+l[1])/2,ie[H]=s.get("nameGap");var ce=new Mr({style:Dr(Ae,{text:s.get("name"),fill:Be,stroke:Oe,lineWidth:x})}),xe=t.add(ce),de=ce.getBoundingRect();o.addSprite(ie,[de.width*R,de.height*R],xe),ce.__idx=this.labelElements.length,this.nameLabelElement=ce}this.labelsMesh.material.set("textureAtlas",t.getTexture()),this.labelsMesh.material.set("uvScale",t.getCoordsScale()),a.convertToTypedArray(),o.convertToTypedArray()};Vi.prototype.setSpriteAlign=function(e,t,r){for(var i=r.getDevicePixelRatio(),n=this.labelsMesh.geometry,a=0;a<this.labelElements.length;a++){var o=this.labelElements[a],s=o.getBoundingRect();n.setSpriteAlign(a,[s.width*i,s.height*i],e,t)}var l=this.nameLabelElement;if(l){var s=l.getBoundingRect();n.setSpriteAlign(l.__idx,[s.width*i,s.height*i],e,t),n.dirty()}this.textAlign=e,this.textVerticalAlign=t};var Zn=Ce.firstNotNull;w.Shader.import(Aa);var Tt={x:0,y:2,z:1};const wu=ho.extend({type:"grid3D",__ecgl__:!0,init:function(e,t){var r=[["y","z","x",-1,"left"],["y","z","x",1,"right"],["x","y","z",-1,"bottom"],["x","y","z",1,"top"],["x","z","y",-1,"far"],["x","z","y",1,"near"]],i=["x","y","z"],n=new w.Material({shader:w.createShader("ecgl.color"),depthMask:!1,transparent:!0}),a=new w.Material({shader:w.createShader("ecgl.meshLines3D"),depthMask:!1,transparent:!0});n.define("fragment","DOUBLE_SIDED"),n.define("both","VERTEX_COLOR"),this.groupGL=new w.Node,this._control=new Ga({zr:t.getZr()}),this._control.init(),this._faces=r.map(function(s){var l=new Wr(s,a,n);return this.groupGL.add(l.rootNode),l},this),this._axes=i.map(function(s){var l=new Vi(s,a);return this.groupGL.add(l.rootNode),l},this);var o=t.getDevicePixelRatio();this._axisLabelSurface=new Ir({width:256,height:256,devicePixelRatio:o}),this._axisLabelSurface.onupdate=function(){t.getZr().refresh()},this._axisPointerLineMesh=new w.Mesh({geometry:new jt({useNativeLine:!1}),material:a,castShadow:!1,ignorePicking:!0,renderOrder:3}),this.groupGL.add(this._axisPointerLineMesh),this._axisPointerLabelsSurface=new Ir({width:128,height:128,devicePixelRatio:o}),this._axisPointerLabelsMesh=new Ui({ignorePicking:!0,renderOrder:4,castShadow:!1}),this._axisPointerLabelsMesh.material.set("textureAtlas",this._axisPointerLabelsSurface.getTexture()),this.groupGL.add(this._axisPointerLabelsMesh),this._lightRoot=new w.Node,this._sceneHelper=new bi,this._sceneHelper.initLight(this._lightRoot)},render:function(e,t,r){this._model=e,this._api=r;var i=e.coordinateSystem;i.viewGL.add(this._lightRoot),e.get("show")?i.viewGL.add(this.groupGL):i.viewGL.remove(this.groupGL);var n=this._control;n.setViewGL(i.viewGL);var a=e.getModel("viewControl");n.setFromViewControlModel(a,0),this._axisLabelSurface.clear(),n.off("update"),e.get("show")&&(this._faces.forEach(function(o){o.update(e,t,r)},this),this._axes.forEach(function(o){o.update(e,this._axisLabelSurface,r)},this)),n.on("update",this._onCameraChange.bind(this,e,r),this),this._sceneHelper.setScene(i.viewGL.scene),this._sceneHelper.updateLight(e),i.viewGL.setPostEffect(e.getModel("postEffect"),r),i.viewGL.setTemporalSuperSampling(e.getModel("temporalSuperSampling")),this._initMouseHandler(e)},afterRender:function(e,t,r,i){var n=i.renderer;this._sceneHelper.updateAmbientCubemap(n,e,r),this._sceneHelper.updateSkybox(n,e,r)},showAxisPointer:function(e,t,r,i){this._doShowAxisPointer(),this._updateAxisPointer(i.value)},hideAxisPointer:function(e,t,r,i){this._doHideAxisPointer()},_initMouseHandler:function(e){var t=e.coordinateSystem,r=t.viewGL;e.get("show")&&e.get("axisPointer.show")?r.on("mousemove",this._updateAxisPointerOnMousePosition,this):r.off("mousemove",this._updateAxisPointerOnMousePosition)},_updateAxisPointerOnMousePosition:function(e){if(!e.target){for(var t=this._model,r=t.coordinateSystem,i=r.viewGL,n=i.castRay(e.offsetX,e.offsetY,new w.Ray),a,o=0;o<this._faces.length;o++){var s=this._faces[o];if(!s.rootNode.invisible){s.plane.normal.dot(i.camera.worldTransform.z)<0&&s.plane.normal.negate();var l=n.intersectPlane(s.plane);if(l){var u=r.getAxis(s.faceInfo[0]),f=r.getAxis(s.faceInfo[1]),h=Tt[s.faceInfo[0]],d=Tt[s.faceInfo[1]];u.contain(l.array[h])&&f.contain(l.array[d])&&(a=l)}}}if(a){var c=r.pointToData(a.array,[],!0);this._updateAxisPointer(c),this._doShowAxisPointer()}else this._doHideAxisPointer()}},_onCameraChange:function(e,t){e.get("show")&&(this._updateFaceVisibility(),this._updateAxisLinePosition());var r=this._control;t.dispatchAction({type:"grid3DChangeCamera",alpha:r.getAlpha(),beta:r.getBeta(),distance:r.getDistance(),center:r.getCenter(),from:this.uid,grid3DId:e.id})},_updateFaceVisibility:function(){var e=this._control.getCamera(),t=new w.Vector3;e.update();for(var r=0;r<this._faces.length/2;r++){for(var i=[],n=0;n<2;n++){var a=this._faces[r*2+n];a.rootNode.getWorldPosition(t),t.transformMat4(e.viewMatrix),i[n]=t.z}var o=i[0]>i[1]?0:1,s=this._faces[r*2+o],l=this._faces[r*2+1-o];s.rootNode.invisible=!0,l.rootNode.invisible=!1}},_updateAxisLinePosition:function(){var e=this._model.coordinateSystem,t=e.getAxis("x"),r=e.getAxis("y"),i=e.getAxis("z"),n=i.getExtentMax(),a=i.getExtentMin(),o=t.getExtentMin(),s=t.getExtentMax(),l=r.getExtentMax(),u=r.getExtentMin(),f=this._axes[0].rootNode,h=this._axes[1].rootNode,d=this._axes[2].rootNode,c=this._faces,v=c[4].rootNode.invisible?u:l,p=c[2].rootNode.invisible?n:a,m=c[0].rootNode.invisible?o:s,_=c[2].rootNode.invisible?n:a,x=c[0].rootNode.invisible?s:o,T=c[4].rootNode.invisible?u:l;f.rotation.identity(),h.rotation.identity(),d.rotation.identity(),c[4].rootNode.invisible&&(this._axes[0].flipped=!0,f.rotation.rotateX(Math.PI)),c[0].rootNode.invisible&&(this._axes[1].flipped=!0,h.rotation.rotateZ(Math.PI)),c[4].rootNode.invisible&&(this._axes[2].flipped=!0,d.rotation.rotateY(Math.PI)),f.position.set(0,p,v),h.position.set(m,_,0),d.position.set(x,0,T),f.update(),h.update(),d.update(),this._updateAxisLabelAlign()},_updateAxisLabelAlign:function(){var e=this._control.getCamera(),t=[new w.Vector4,new w.Vector4],r=new w.Vector4;this.groupGL.getWorldPosition(r),r.w=1,r.transformMat4(e.viewMatrix).transformMat4(e.projectionMatrix),r.x/=r.w,r.y/=r.w,this._axes.forEach(function(i){var n=i.axisLineCoords;i.labelsMesh.geometry;for(var a=0;a<t.length;a++)t[a].setArray(n[a]),t[a].w=1,t[a].transformMat4(i.rootNode.worldTransform).transformMat4(e.viewMatrix).transformMat4(e.projectionMatrix),t[a].x/=t[a].w,t[a].y/=t[a].w;var o=t[1].x-t[0].x,s=t[1].y-t[0].y,l=(t[1].x+t[0].x)/2,u=(t[1].y+t[0].y)/2,f,h;Math.abs(s/o)<.5?(f="center",h=u>r.y?"bottom":"top"):(h="middle",f=l>r.x?"left":"right"),i.setSpriteAlign(f,h,this._api)},this)},_doShowAxisPointer:function(){this._axisPointerLineMesh.invisible&&(this._axisPointerLineMesh.invisible=!1,this._axisPointerLabelsMesh.invisible=!1,this._api.getZr().refresh())},_doHideAxisPointer:function(){this._axisPointerLineMesh.invisible||(this._axisPointerLineMesh.invisible=!0,this._axisPointerLabelsMesh.invisible=!0,this._api.getZr().refresh())},_updateAxisPointer:function(e){var t=this._model.coordinateSystem,r=t.dataToPoint(e),i=this._axisPointerLineMesh,n=i.geometry,a=this._model.getModel("axisPointer"),o=this._api.getDevicePixelRatio();n.convertToDynamicArray(!0);function s(A){return Ce.firstNotNull(A.model.get("axisPointer.show"),a.get("show"))}function l(A){var N=A.model.getModel("axisPointer",a),H=N.getModel("lineStyle"),R=w.parseColor(H.get("color")),U=Zn(H.get("width"),1),V=Zn(H.get("opacity"),1);return R[3]*=V,{color:R,lineWidth:U}}for(var u=0;u<this._faces.length;u++){var f=this._faces[u];if(!f.rootNode.invisible){for(var h=f.faceInfo,d=h[3]<0?t.getAxis(h[2]).getExtentMin():t.getAxis(h[2]).getExtentMax(),c=Tt[h[2]],v=0;v<2;v++){var p=h[v],m=h[1-v],_=t.getAxis(p),x=t.getAxis(m);if(s(_)){var T=[0,0,0],g=[0,0,0],E=Tt[p],S=Tt[m];T[E]=g[E]=r[E],T[c]=g[c]=d,T[S]=x.getExtentMin(),g[S]=x.getExtentMax();var C=l(_);n.addLine(T,g,C.color,C.lineWidth*o)}}if(s(t.getAxis(h[2]))){var T=r.slice(),g=r.slice();g[c]=d;var C=l(t.getAxis(h[2]));n.addLine(T,g,C.color,C.lineWidth*o)}}}n.convertToTypedArray(),this._updateAxisPointerLabelsMesh(e),this._api.getZr().refresh()},_updateAxisPointerLabelsMesh:function(e){var t=this._model,r=this._axisPointerLabelsMesh,i=this._axisPointerLabelsSurface,n=t.coordinateSystem,a=t.getModel("axisPointer");r.geometry.convertToDynamicArray(!0),i.clear();var o={x:"y",y:"x",z:"y"};this._axes.forEach(function(s,l){var u=n.getAxis(s.dim),f=u.model,h=f.getModel("axisPointer",a),d=h.getModel("label"),c=h.get("lineStyle.color");if(!(!d.get("show")||!h.get("show"))){var v=e[l],p=d.get("formatter"),m=u.scale.getLabel({value:v});if(p!=null)m=p(m,e);else if(u.scale.type==="interval"||u.scale.type==="log"){var _=co(u.scale.getTicks()[0]);m=v.toFixed(_+2)}var x=d.get("color"),T=new Mr({style:Dr(d,{text:m,fill:x||c,align:"left",verticalAlign:"top"})}),g=i.add(T),E=T.getBoundingRect(),S=this._api.getDevicePixelRatio(),C=s.rootNode.position.toArray(),A=Tt[o[s.dim]];C[A]+=(s.flipped?-1:1)*d.get("margin"),C[Tt[s.dim]]=u.dataToCoord(e[l]),r.geometry.addSprite(C,[E.width*S,E.height*S],g,s.textAlign,s.textVerticalAlign)}},this),i.getZr().refreshImmediately(),r.material.set("uvScale",i.getCoordsScale()),r.geometry.convertToTypedArray()},dispose:function(){this.groupGL.removeAll(),this._control.dispose(),this._axisLabelSurface.dispose(),this._axisPointerLabelsSurface.dispose()}});function hr(e){ta.call(this,e),this.type="cartesian3D",this.dimensions=["x","y","z"],this.size=[0,0,0]}hr.prototype={constructor:hr,model:null,containPoint:function(e){return this.getAxis("x").contain(e[0])&&this.getAxis("y").contain(e[2])&&this.getAxis("z").contain(e[1])},containData:function(e){return this.getAxis("x").containData(e[0])&&this.getAxis("y").containData(e[1])&&this.getAxis("z").containData(e[2])},dataToPoint:function(e,t,r){return t=t||[],t[0]=this.getAxis("x").dataToCoord(e[0],r),t[2]=this.getAxis("y").dataToCoord(e[1],r),t[1]=this.getAxis("z").dataToCoord(e[2],r),t},pointToData:function(e,t,r){return t=t||[],t[0]=this.getAxis("x").coordToData(e[0],r),t[1]=this.getAxis("y").coordToData(e[2],r),t[2]=this.getAxis("z").coordToData(e[1],r),t}};ra(hr,ta);function zr(e,t,r){ia.call(this,e,t,r)}zr.prototype={constructor:zr,getExtentMin:function(){var e=this._extent;return Math.min(e[0],e[1])},getExtentMax:function(){var e=this._extent;return Math.max(e[0],e[1])},calculateCategoryInterval:function(){return Math.floor(this.scale.count()/8)}};ra(zr,ia);function bu(e,t){var r=e.getBoxLayoutParams(),i=vo(r,{width:t.getWidth(),height:t.getHeight()});i.y=t.getHeight()-i.y-i.height,this.viewGL.setViewport(i.x,i.y,i.width,i.height,t.getDevicePixelRatio());var n=e.get("boxWidth"),a=e.get("boxHeight"),o=e.get("boxDepth");this.getAxis("x").setExtent(-n/2,n/2),this.getAxis("y").setExtent(o/2,-o/2),this.getAxis("z").setExtent(-a/2,a/2),this.size=[n,a,o]}function Au(e,t){var r={};function i(n,a){r[n]=r[n]||[1/0,-1/0],r[n][0]=Math.min(a[0],r[n][0]),r[n][1]=Math.max(a[1],r[n][1])}e.eachSeries(function(n){if(n.coordinateSystem===this){var a=n.getData();["x","y","z"].forEach(function(o){a.mapDimensionsAll(o,!0).forEach(function(s){i(o,a.getDataExtent(s,!0))})})}},this),["xAxis3D","yAxis3D","zAxis3D"].forEach(function(n){e.eachComponent(n,function(a){var o=n.charAt(0),s=a.getReferringComponents("grid3D").models[0],l=s.coordinateSystem;if(l===this){var u=l.getAxis(o);if(!u){var f=po(r[o]||[1/0,-1/0],a);u=new zr(o,f),u.type=a.get("type");var h=u.type==="category";u.onBand=h&&a.get("boundaryGap"),u.inverse=a.get("inverse"),a.axis=u,u.model=a,u.getLabelModel=function(){return a.getModel("axisLabel",s.getModel("axisLabel"))},u.getTickModel=function(){return a.getModel("axisTick",s.getModel("axisTick"))},l.addAxis(u)}}},this)},this),this.resize(this.model,t)}var Cu={dimensions:hr.prototype.dimensions,create:function(e,t){var r=[];e.eachComponent("grid3D",function(a){a.__viewGL=a.__viewGL||new se;var o=new hr;o.model=a,o.viewGL=a.__viewGL,a.coordinateSystem=o,r.push(o),o.resize=bu,o.update=Au});var i=["xAxis3D","yAxis3D","zAxis3D"];function n(a,o){return i.map(function(s){var l=a.getReferringComponents(s).models[0];return l==null&&(l=o.getComponent(s)),l})}return e.eachSeries(function(a){if(a.get("coordinateSystem")==="cartesian3D"){var o=a.getReferringComponents("grid3D").models[0];if(o==null){var s=n(a,e),o=s[0].getCoordSysModel();s.forEach(function(f){f.getCoordSysModel()})}var l=o.coordinateSystem;a.coordinateSystem=l}}),r}},Wa=ea.extend({type:"cartesian3DAxis",axis:null,getCoordSysModel:function(){return this.ecModel.queryComponents({mainType:"grid3D",index:this.option.gridIndex,id:this.option.gridId})[0]}});mo(Wa);var Xa={show:!0,grid3DIndex:0,inverse:!1,name:"",nameLocation:"middle",nameTextStyle:{fontSize:16},nameGap:20,axisPointer:{},axisLine:{},axisTick:{},axisLabel:{},splitArea:{}},Lu=it({boundaryGap:!0,axisTick:{alignWithLabel:!1,interval:"auto"},axisLabel:{interval:"auto"},axisPointer:{label:{show:!1}}},Xa),Gi=it({boundaryGap:[0,0],splitNumber:5,axisPointer:{label:{}}},Xa),Mu=Ct({scale:!0,min:"dataMin",max:"dataMax"},Gi),qa=Ct({logBase:10},Gi);qa.scale=!0;const Du={categoryAxis3D:Lu,valueAxis3D:Gi,timeAxis3D:Mu,logAxis3D:qa};var Pu=["value","category","time","log"];function Nu(e,t,r,i,n){Pu.forEach(function(a){var o=r.extend({type:t+"Axis3D."+a,__ordinalMeta:null,mergeDefaultAndTheme:function(s,l){var u=l.getTheme();it(s,u.get(a+"Axis3D")),it(s,this.getDefaultOption()),s.type=i(t,s)},optionUpdated:function(){var s=this.option;s.type==="category"&&(this.__ordinalMeta=go.createByAxisModel(this))},getCategories:function(){if(this.option.type==="category")return this.__ordinalMeta.categories},getOrdinalMeta:function(){return this.__ordinalMeta},defaultOption:it(_o(Du[a+"Axis3D"]),n||{},!0)});e.registerComponentModel(o)}),e.registerSubTypeDefaulter(t+"Axis3D",yo(i,t))}function Ru(e,t){return t.type||(t.data?"category":"value")}function Uu(e){e.registerComponentModel(kr),e.registerComponentView(wu),e.registerCoordinateSystem("grid3D",Cu),["x","y","z"].forEach(function(t){Nu(e,t,Wa,Ru,{name:t.toUpperCase()});const r=e.ComponentView.extend({type:t+"Axis3D"});e.registerComponentView(r)}),e.registerAction({type:"grid3DChangeCamera",event:"grid3dcamerachanged",update:"series:updateCamera"},function(t,r){r.eachComponent({mainType:"grid3D",query:t},function(i){i.setView(t)})}),e.registerAction({type:"grid3DShowAxisPointer",event:"grid3dshowaxispointer",update:"grid3D:showAxisPointer"},function(t,r){}),e.registerAction({type:"grid3DHideAxisPointer",event:"grid3dhideaxispointer",update:"grid3D:hideAxisPointer"},function(t,r){})}export{Bu as a,Fu as b,Uu as c,Iu as i};
