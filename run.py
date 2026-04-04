from src.index import app

if __name__ == '__main__':
    app.run(
        debug=True,
        dev_tools_ui=False,
        dev_tools_hot_reload=False,
        port=8052,
        host="127.0.0.1",
    )
