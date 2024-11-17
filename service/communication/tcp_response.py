''' test route '''
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"



'''
TODOs aus dem Blatt 
'''
''' stern routes '''

#TODO: POST /vs/v1/system/
#TODO: PATCH /vs/v1/system/<COM-UUID>
#TODO: GET /vs/v1/system/<COM-UUID>?star=<STAR-UUID>
#TODO: DELETE /vs/v1/system/<COM-UUID>?star=<STAR-UUID>

''' messaging routes '''

#TODO: POST /vs/v1/messages/<MSG-UUID>
#TODO: DELETE /vs/v1/messages/<MSG-UUID>?star=<STAR-UUID>
#TODO: GET /vs/v1/messages?star=<STAR-UUID>&scope=<SCOPE>&info=<INFO>
#TODO: GET /vs/v1/messages/<MSG-UUID>?star=<STAR-UUID>