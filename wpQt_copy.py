import requests
from PyQt5 import QtCore, QtGui, QtWidgets
import openai
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from googletrans import Translator
import requests


class Worker(QThread):
    taskFinished = pyqtSignal(str, bool)

    def __init__(self, mainWindow):
        QThread.__init__(self)
        self.mainWindow = mainWindow

    @QtCore.pyqtSlot()
    def run(self):
        try:
            topics_list = self.mainWindow.generate_topics()
            self.mainWindow.show_topics_list(topics_list)
            self.mainWindow.postToWordPress(topics_list)
            self.taskFinished.emit("성공적으로 글이 게시되었습니다!", True)
        except Exception as err:
            self.taskFinished.emit(str(err), False)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Auto Posting")
        self.resize(500, 800)
        self.setupUi()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.start_worker)


    def addRow(self, formLayout, labelText, echoMode=None):
        label = QtWidgets.QLabel(self.centralwidget)
        label.setText(labelText)
        lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        if echoMode:
            lineEdit.setEchoMode(echoMode)
        formLayout.addRow(label, lineEdit)
        return lineEdit
    

    def show_usage(self):
        usage_text = "<h3><CENTER>How to Use</CENTER></h3><br>"
        usage_text += "<p style='font-size: 15px;'>1. 'Topic' 필드에 블로그 주제를 입력합니다. 여러 주제를 입력하려면 쉼표로 구분합니다. (ex. 주제1, 주제2, 주제3)</p><br>"
        usage_text += "<p style='font-size: 15px;'>2. 'API Key' 필드에 OpenAI API 키를 입력합니다.</p><br>"
        usage_text += "<p style='font-size: 15px;'>3. 'WordPress Username'과 'WordPress Password' 필드에 WordPress 계정 정보를 입력합니다.</p><br>"
        usage_text += "<p style='font-size: 15px;'>4. 'WordPress URL' 필드에 WordPress 사이트 URL을 입력합니다. (URL의 마지막에 '/'는 포함하지 않습니다)</p><br>"
        usage_text += "<p style='font-size: 15px;'>5. 'Number of Posting' 스핀 박스에서 게시할 포스팅 개수를 선택합니다.</p><br>"
        usage_text += "<p style='font-size: 15px;'>6. 'Enable Auto Posting' 체크박스를 선택하고 자동 게시 간격을 설정하면 일정 시간마다 포스팅이 자동으로 게시됩니다.</p><br>"
        usage_text += "<p style='font-size: 15px;'>7. 'Run' 버튼을 클릭하여 포스팅 작성 및 게시를 시작합니다.</p><br>"
        usage_text += "<p style='font-size: 15px;'><b>※ 주의사항:</b> 프로그램을 사용하기 전에 OpenAI API 키와 WordPress 계정 정보를 정확히 입력해야 합니다.</p><br>"

        QMessageBox.information(self, "How to Use", usage_text)





    def setupUi(self):
        self.centralwidget = QtWidgets.QWidget(self)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(20)

        self.descLabel = QtWidgets.QLabel(self.centralwidget)
        self.descLabel.setText("<CENTER><h1>AutoPosting v0.2.0</CENTER></h1>")
        self.descLabel.setWordWrap(True)
        self.verticalLayout.addWidget(self.descLabel)

        self.resultTextBox = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.verticalLayout.addWidget(self.resultTextBox)

        formLayout = QtWidgets.QFormLayout()
        formLayout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        formLayout.setFormAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)



        self.topicLineEdit = self.addRow(formLayout, "Topic: ")
        self.apiKeyLineEdit = self.addRow(formLayout, "API Key:", QtWidgets.QLineEdit.Password)
        self.usernameLineEdit = self.addRow(formLayout, "WordPress Username:")
        self.passwordLineEdit = self.addRow(formLayout, "WordPress Password:", QtWidgets.QLineEdit.Password)
        self.wpUrlLineEdit = self.addRow(formLayout, "WordPress URL:")

        self.numberLabel = QtWidgets.QLabel(self.centralwidget)
        self.numberLabel.setText("Number of Posting:")

        self.numberSpinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.numberSpinBox.setRange(2, 10)
        self.numberSpinBox.setValue(2)

        formLayout.addRow(self.numberLabel, self.numberSpinBox)

        self.autoPostCheckBox = QtWidgets.QCheckBox("Enable Auto Posting", self.centralwidget)
        self.autoPostIntervalSpinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.autoPostIntervalSpinBox.setRange(1, 60)
        self.autoPostIntervalSpinBox.setSuffix(' min')
        self.autoPostIntervalSpinBox.setValue(30)
        formLayout.addRow(self.autoPostCheckBox, self.autoPostIntervalSpinBox)

        self.verticalLayout.addLayout(formLayout)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacer)

        self.autoPostCheckBox.stateChanged.connect(self.check_auto_posting)
        self.autoPostIntervalSpinBox.valueChanged.connect(self.check_auto_posting)

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.verticalLayout.addWidget(self.progressBar)

        self.postButton = QtWidgets.QPushButton(self.centralwidget)
        self.postButton.setText("Run")
        self.verticalLayout.addWidget(self.postButton)

        self.usageButton = QtWidgets.QPushButton(self.centralwidget)
        self.usageButton.setText("How to Use")
        self.usageButton.setStyleSheet(
            '''
            QPushButton {
                font-size: 18px;
                color: white;
                background-color: #4287f5;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            '''
        )
        self.verticalLayout.addWidget(self.usageButton)


        self.setCentralWidget(self.centralwidget)

        self.postButton.clicked.connect(self.start_worker)
        self.usageButton.clicked.connect(self.show_usage)

        self.setStyleSheet("""
            QLabel {
                font-size: 20px;
                text-align: center;
            }
            QLineEdit {
                background-color: #f2f2f2;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                font-size: 20px;
                color: white;
                background-color: #4287f5;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPlainTextEdit {
                background-color: #f2f2f2;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QProgressBar {
                background-color: #f2f2f2;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 1px;
                text-align: center;
            }
            QSpinBox {
                background-color: #f2f2f2;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QCheckBox {
                font-size: 20px;
                color: #000000;
            }
        """)


    def setupTimer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.start_worker)

    @QtCore.pyqtSlot()
    def check_auto_posting(self):
        if self.autoPostCheckBox.isChecked():
            interval = self.autoPostIntervalSpinBox.value() * 60000  # convert minutes to milliseconds
            self.timer.start(interval)
        else:
            self.timer.stop()


    def postToWordPress(self, topics_list):
        post_count = int(self.numberSpinBox.value())
        api_key = self.apiKeyLineEdit.text()
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()
        wp_url = self.wpUrlLineEdit.text()

        openai.api_key = api_key

        progress_step = 100 // post_count

        for i, topic in enumerate(topics_list, start=1):
            content = self.generate_content(topic)
            self.create_wordpress_post(topic, content, username, password, wp_url)
            self.progressBar.setValue(i * progress_step)


    def create_wordpress_post(self, topic, content, username, password, wp_url):
        #user_topic = self.topicLineEdit.text().split(',')
        translator = Translator()
        translated_topic = translator.translate(topic, dest='en').text
        image_url = f"https://source.unsplash.com/featured/?{translated_topic}"

        wordpress_url = wp_url + '/wp-json/wp/v2/posts'

        headers = {
            'Content-Type': 'application/json',
        }

        data = {
            'title': topic,
            'content': f'<img src="{image_url}">\n\n{content}',
            'status': 'publish',
        }

        response = requests.post(wordpress_url, headers=headers, json=data, auth=(username, password))
        response.raise_for_status()


    def generate_content(self, topic):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "당신은 이제부터 파워블로거 입니다. 사용자가 요구하는 주제에 관련된 블로그 포스팅을 작성하는것이 당신의 역할입니다. 블로그 포스팅의 본문내용만을 작성해야합니다. 본문 내용 외 다른 목차는 작성하지 않습니다. 분량은 최대한 길고 자세하게 작성하세요."},
                {"role": "user", "content": f"주제는  {topic} 입니다.  {topic} + 에 대한 블로그 글을 작성해주세요. "}
            ]
        )
        return completion.choices[0].message['content']

    def generate_topics(self):
        topics = self.topicLineEdit.text().split(',')
        count = int(self.numberSpinBox.value())
        entire_topic_list = []

        for topic in topics:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                    "content": f"당신은 이제부터 블로그 주제를 생성하는 역할을 맡습니다. 사용자가 제시하는 대주제에 대해 블로그 포스팅 주제를 정하고 핵심 블로그 포스팅 제목만 출력합니다. 각 주제는 개행으로 구별되며, {count}개의 포스팅 주제를 출력하세요. 부제는 입력하지 않습니다."},
                    {"role": "user", "content": f"{topic}에 대한 {count}개의 블로그 주제를 생성해주세요."}
                ]
            )
            topics_str = completion.choices[0].message['content']
            topics_list = [topic.replace('\"', '').strip() for topic in topics_str.split('\n') if topic.strip()]

            if topics_list:
                topics_str_without_number = '\n'.join([topic.split('. ')[1] for topic in topics_list])
                topics_list_without_number = [topic for topic in topics_str_without_number.split('\n') if topic.strip()]
                entire_topic_list.extend(topics_list_without_number)
    
        return entire_topic_list



    def show_topics_list(self, topics_list):
        topics_str = '\n'.join(topics_list)
        self.resultTextBox.appendPlainText(topics_str)

    def start_worker(self):
        topic = self.topicLineEdit.text()
        api_key = self.apiKeyLineEdit.text()
        post_count = int(self.numberSpinBox.text())  # 수정된 부분
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()
        wp_url = self.wpUrlLineEdit.text()
        if not all([topic, api_key, post_count, username, password, wp_url]):
            self.resultTextBox.appendPlainText("실패: 모든 필드를 유효한 값으로 채워주세요.")
            return
        openai.api_key = api_key

        self.postButton.setEnabled(False)
        self.topicLineEdit.setEnabled(False)
        self.apiKeyLineEdit.setEnabled(False)
        self.usernameLineEdit.setEnabled(False)
        self.passwordLineEdit.setEnabled(False)
        self.wpUrlLineEdit.setEnabled(False)
        self.numberSpinBox.setEnabled(False)

        self.progressBar.setValue(0)

        self.worker = Worker(self)  
        self.worker.taskFinished.connect(self.handle_results)
        self.worker.start()




    @QtCore.pyqtSlot(str, bool)
    def handle_results(self, result, status):
        if status:
            self.resultTextBox.appendPlainText(f"\n{result}")
        else:
            self.resultTextBox.appendPlainText(f"\n실패: {result}")

        self.postButton.setEnabled(True)
        self.topicLineEdit.setEnabled(True)
        self.apiKeyLineEdit.setEnabled(True)
        self.usernameLineEdit.setEnabled(True)
        self.passwordLineEdit.setEnabled(True)
        self.wpUrlLineEdit.setEnabled(True)
        self.numberSpinBox.setEnabled(True)

if __name__ == "__main__":
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())