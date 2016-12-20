from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin, current_user
from . import db, login_manager
from os.path import exists


class Permission:
    Enter_Page = 0x01
    ADMINISTER = 0x80
    Read_Self_Arch = 0x04


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(16), unique=True)
    permissions = db.Column(db.Integer)
    default = db.Column(db.Boolean, default=False, index=True)
    # ForeignKey
    users = db.relationship('User', backref='role', lazy='dynamic')

    # Refresh Role
    @staticmethod
    def insert_roles():
        roles = {
            'People': (Permission.Enter_Page, True),
            'Student': (Permission.Enter_Page |
                        Permission.Read_Self_Arch, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    email = db.Column(db.VARCHAR(64), index=True)
    username = db.Column(db.VARCHAR(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.VARCHAR(128))
    student_id = db.Column(db.Integer, db.ForeignKey('archives.student_id'), unique=True)
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.VARCHAR(64))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    pic = db.Column(db.VARCHAR(45))
    # ForeignKey
    logs = db.relationship('Log', backref='user', lazy='dynamic')
    internal_mail = db.relationship('Internal_mail')

    # archives_management_system
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    # Update old User`s Role
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            elif self.student_id is not None and self.role is None:
                self.role = Role.query.filter_by(name='Student').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def __repr__(self):
        return '<User %r>' % self.username

    def is_people(self):
        if self.role_id == 2:
            return True
        else:
            return False

    def is_student(self):
        if self.role_id == 3:
            return True
        else:
            return False

    def get_pic(self):
        if self.pic == '1':
            path = '/home/liuyu/PycharmProjects/archives_management_system/app/static/images/user/' + str(
                id) + '.jpg'
            temp = 1
        elif self.student_id:
            path = '/home/liuyu/PycharmProjects/archives_management_system/app/static/images/' + str(
                self.student_id) + '.jpg'
            temp = 2
        else:
            path = 'images/profile_small.jpg'
            temp = 3
        if temp < 3 and exists(path):
            if temp == 1:
                return 'images/user/' + str(id) + '.jpg'
            else:
                return 'images/' + str(self.student_id) + '.jpg'
        else:
            return 'images/profile_small.jpg'

    def get_role(self):
        dict = {'1': '管理员',
                '3': '学生',
                '2': '普通用户'}
        return dict[str(self.role_id)]

    @staticmethod
    def get_mail():
        return Internal_mail.query.filter_by(receiver=current_user.id, receiver_delete=False)

    @staticmethod
    def get_mail_num():
        return Internal_mail.query.filter_by(receiver=current_user.id, receiver_delete=False).count()

    @staticmethod
    def get_unread_mail_num():
        return Internal_mail.query.filter_by(receiver=current_user.id, read=False, receiver_delete=False).count()

    @staticmethod
    def get_unread_mail():
        return Internal_mail.query.filter_by(receiver=current_user.id, read=False, receiver_delete=False)

    @staticmethod
    def get_mail_send():
        return Internal_mail.query.filter_by(sender=current_user.id, sender_delete=False)


class AnonymousUser(AnonymousUserMixin):
    @staticmethod
    def can(permissions):
        return False

    @staticmethod
    def is_administrator():
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Archive(db.Model):
    __tablename__ = 'archives'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(8), index=True)
    age = db.Column(db.Integer)
    birth = db.Column(db.DATE)
    sex = db.Column(db.VARCHAR(4))
    address = db.Column(db.VARCHAR(32))
    academy = db.Column(db.VARCHAR(32))
    grade = db.Column(db.VARCHAR(4))
    political_status = db.Column(db.VARCHAR(8))
    ID_number = db.Column(db.VARCHAR(32))
    student_id = db.Column(db.Integer, nullable=False, index=True, unique=True)
    nation = db.Column(db.VARCHAR(8), default='汉族')
    email = db.Column(db.VARCHAR(64), unique=True)
    archive_status = db.Column(db.SMALLINT, default=0)
    enrollment_time = db.Column(db.DATE, default=datetime.utcnow())
    status = db.Column(db.Integer, default=1)
    delete = db.Column(db.BOOLEAN, default=False)
    delete_expire_date = db.Column(db.DATE)
    # ForeignKey
    users = db.relationship('User', backref='archive', lazy='dynamic')
    archive_apply = db.relationship('Archive_Apply', backref='archive', lazy='dynamic')
    log = db.relationship('Log', backref='archive', lazy='dynamic')

    @staticmethod
    def new_archive(archive):
        db.session.add(archive)
        db.session.commit()
        user = User(name=archive.name, student_id=archive.student_id,
                    email=archive.email if archive.email is not None else '',
                    password='123456')
        db.session.add(user)
        db.session.commit()

    def get_pic(self):
        path = '/home/liuyu/PycharmProjects/archives_management_system/app/static/images/' + str(
            self.student_id) + '.jpg'
        if exists(path):
            return 'images/' + str(self.student_id) + '.jpg'
        else:
            return 'images/profile_big.jpg'

    def get_status(self):
        if self.status == 1:
            return '在库'
        else:
            return '借出'


class Log(db.Model):
    __tablename__ = 'logs'
    archive_id = db.Column(db.Integer, db.ForeignKey('archives.id'), primary_key=True, )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow())


class Archive_Apply(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow())
    applicant = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('archives.student_id'), nullable=False)
    apply_type = db.Column(db.SMALLINT)
    describe = db.Column(db.Text)
    status = db.Column(db.SMALLINT, default=False)
    # status 0:not processed
    # status 1:admit
    # status 2:forbid
    # status 3:return
    operator = db.Column(db.Integer)
    process_date = db.Column(db.DATETIME)
    forbid_reason = db.Column(db.Text)
    expiry_date = db.Column(db.DATETIME)
    expiry = db.Column(db.BOOLEAN, default=False)
    apply_taken_confirm = db.Column(db.SMALLINT, default=0)

    def get_apply_name(self):
        return User.query.filter_by(id=self.applicant).first().name

    def get_archive_status(self):
        archive = Archive.query.filter_by(student_id=self.student_id).first()
        if archive is None:
            return '档案不存在'
        status = {1: '在库',
                  0: '借出'}
        return status[archive.status]

    def available(self):
        if self.expiry_date > datetime.utcnow():
            return True
        else:
            return False

    def get_apply_type(self):
        type = {1: '电子档案',
                2: '实体档案'}
        return type[self.apply_type]

    def get_applicant_name(self):
        return User.query.filter_by(id=self.applicant).first().name


class Internal_mail(db.Model):
    __tablename__ = 'internal_mail'
    id = db.Column(db.Integer, primary_key=True)
    send_time = db.Column(db.DATETIME, default=datetime.utcnow())
    sender = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver = db.Column(db.Integer, index=True)
    sender_delete = db.Column(db.BOOLEAN, default=False)
    receiver_delete = db.Column(db.BOOLEAN, default=False)
    subject = db.Column(db.VARCHAR(45))
    body = db.Column(db.Text)
    status = db.Column(db.Integer, default=False)
    read = db.Column(db.BOOLEAN, default=False)

    def get_sender_name(self):
        return User.query.filter_by(id=self.sender).first().name

    def get_receiver_name(self):
        return User.query.filter_by(id=self.receiver).first().name


class mail_status:
    send = 0
    send_read = 1
    drafts = 2


