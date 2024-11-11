前端：在前端目录下npm run build
    npm run serve
后端：在后端目录下uvicorn main:app --reload --port 9000

好像使用axios那个库可以把前后端绑在一起，运行后端直接出前端的界面，应该是build以后前端生成了一个index.html
然后后端绑住了那个html

还是采用前后端分离吧 现在需要开两个terminal 一个在vue-frontend目录下 一个在后端目录下 port改成了8001 因为好像前后端端口不能一样 同时前端请求的代码(await fetch)要和后端端口一样