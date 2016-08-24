from flask import Flask
app_lulu = Flask(__name__)

@app_lulu.route('/hello_page_lulu')
def hello_world_lulu():
    # this is a comment, just like in Python
    # note that the function name and the route argument
    # do not need to be the same.
    return 'Hello world!'
    
if __name__ == '__main__':
#	app_lulu.run(port=33507)
       app_lulu.run()
