# -*- coding: UTF-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request, \
    current_app, make_response
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, SearchArchiveForm, ArchiveInfoForm, SearchUserForm, \
    ComposeMailForm, SearchApplicantForm, DeleteForm, ArchiveApplyForm, ArchiveApplyProcessForm, batch_managementForm
from .. import db
from ..models import Log, Permission, Role, User, Archive, Internal_mail, Archive_Apply
from ..decorators import admin_required, permission_required
import os, xlrd, csv, re, calendar
from werkzeug.utils import secure_filename
from datetime import datetime
import pymysql

path_archive = '/home/liuyu/PycharmProjects/archives_management_system/app/static/temp'
path_img = '/home/liuyu/PycharmProjects/archives_management_system/app/static/images'


def set_expire_date():
    now = datetime.utcnow()
    days = calendar.monthrange(now.year, now.month)[1]
    if now.day + 7 > days:
        if now.month + 1 > 12:
            return now.replace(year=now.year + 1, day=7 - days + now.day)
        else:
            return now.replace(month=now.month + 1, day=7 - days + now.day)
    else:
        return now.replace(day=now.day + 7)


@main.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_administrator():
        return redirect(url_for('.index_admin'))
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    now = datetime.utcnow()
    applys = Archive_Apply.query.filter_by(expiry=False, status=1)
    if applys.count() > 0:
        for archive in applys:
            if now > archive.expiry_date:
                log = Log(date=datetime.utcnow(),
                          user_id=archive.applicant,
                          archive_id=archive.student_id)
                archive.expiry = True
                db.session.add(log)
                db.session.add(archive)
                db.session.commit()
    form = SearchArchiveForm()
    content = Archive.query.filter().all
    return render_template('index_user.html', form=form, content=content, select_main=1)


@main.route('/Admin', methods=['GET', 'POST'])
@admin_required
def index_admin():
    return render_template('index_admin.html')


@main.route('/show_all', methods=['GET', 'POST'])
@admin_required
def show_all():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    form = SearchArchiveForm()
    archives = Archive.query.filter_by(delete=False)
    type = '所有档案'
    if form.validate_on_submit():
        if not form.key_words.data == '':
            if form.name.data == 'Name':
                archives = Archive.query.filter_by(name=form.key_words.data)
            else:
                archives = Archive.query.filter_by(student_id=form.key_words.data)
            type = '搜索结果'
            flash('搜索完毕,共找到' + str(archives.count()) + '条结果')
        else:
            archives = Archive.query.filter_by()
            type = '所有档案'
    return render_template('All_Archive.html', form=form, archives=archives, type=type, select_main=2, select_second=1)


@main.route('/import_multi', methods=['GET', 'POST'])
@admin_required
def import_multi():
    form = SearchArchiveForm()
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    message = ''
    if request.method == 'POST':
        file = request.files['file']
        if file:
            fname = secure_filename(file.filename)
            file.save(os.path.join(path_archive, fname))
            num = process_csv(fname)
            flash('导入成功，共导入' + str(num) + '份档案')
    return render_template('import_file_multi.html', message=message, form=form, select_main=2, select_second=2,
                           select_third=2)


def process_csv(fname):
    num = 0
    with open(path_archive + '/' + str(fname)) as csvfile:
        reader = [each for each in csv.DictReader(csvfile)]
        for person in reader:
            num += 1
            archive = Archive(name=person['name'],
                              sex=person['sex'],
                              academy=person['academy'],
                              student_id=person['student_id'],
                              political_status=person['political_status'],
                              ID_number=person['ID_number'],
                              nation=person['nation'],
                              grade=person['student_id'][0:4]
                              )
            Archive.new_archive(archive=archive)
    os.remove(path_archive + '/' + fname)
    return num


@main.route('/import_single', methods=['GET', 'POST'])
@admin_required
def import_single():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    form = ArchiveInfoForm()
    if form.submit() and form.name.data:
        archive = Archive(name=form.name.data,
                          sex=form.sex.data,
                          birth=re.sub('-', '/', form.birth.data),
                          age=form.age.data,
                          address=form.address.data,
                          grade=form.grade.data,
                          political_status=form.political_status.data,
                          ID_number=re.sub('-', '', form.ID_number.data),
                          nation=form.nation.data,
                          academy=form.academy.data,
                          student_id=int(re.sub('-', '', form.student_id.data)),
                          email=form.email.data
                          )
        Archive.new_archive(archive=archive)
        flash('新建档案成功')
    return render_template('import_file_single.html', form=form, select_main=2, select_second=2, select_third=1)


@main.route('/archive_info/<int:student_id>', methods=['GET', 'POST'])
@login_required
def archive_info(student_id):
    if current_user.is_people() or (current_user.is_student() and current_user.student_id != student_id):
        abort(403)
    form = ArchiveInfoForm()
    archive = Archive.query.filter_by(student_id=student_id).first()
    path = '/home/liuyu/PycharmProjects/archives_management_system/app/static/images/' + str(
        student_id) + '.jpg'
    if os.path.exists(path):
        dir = 'images/' + str(student_id) + '.jpg'
    else:
        dir = 'images/profile_big.jpg'
    return render_template('Archive_profile.html', archive=archive, dir=dir, form=form, select_main=2, select_second=1)


@main.route('/archive/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def archive_edit(student_id):
    form = ArchiveInfoForm()
    archive = Archive.query.filter_by(student_id=student_id, delete=False).first()
    path = '/home/liuyu/PycharmProjects/archives_management_system/app/static/images/' + str(
        student_id) + '.jpg'
    if os.path.exists(path):
        dir = 'images/' + str(student_id) + '.jpg'
    else:
        dir = 'images/profile_big.jpg'
    if form.submit.data:
        archive.name = form.name.data
        archive.birth = form.birth.data
        archive.age = form.age.data
        archive.address = form.address.data
        archive.political_status = form.political_status.data
        archive.academy = form.academy.data
        archive.student_id = form.student_id.data
        archive.email = form.email.data
        db.session.add(archive)
        db.session.commit()
        flash('修改成功')
        return redirect(url_for('.archive_edit', student_id=student_id))
    if form.delete.data:
        archive.delete = True
        archive.delete_expire_date = set_expire_date()
        db.session.add(archive)
        db.session.commit()
        flash('已删除')
        return redirect(url_for('.show_all'))
    return render_template('Archive_profile.html', archive=archive, dir=dir, form=form, type=0)


@main.route('/archive_recycle_bin', methods=['GET', 'POST'])
@admin_required
def archive_recycle_bin():
    form = SearchArchiveForm()
    archives = Archive.query.filter_by(delete=True)
    if archives.count() > 0:
        for archive in archives:
            if datetime.utcnow().date() > archive.delete_expire_date:
                db.session.delete(archive)
                db.session.commit()
                archives = Archive.query.filter_by(delete=True)
    return render_template('Archive_recycle_bin.html', archives=archives, form=form, type='回收站', select_main=2,
                           select_second=3)


@main.route('/RecoveryEdit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def archive_recycle_bin_edit(student_id):
    form = ArchiveInfoForm()
    archive = Archive.query.filter_by(student_id=student_id).first()
    if form.recovery.data:
        archive.delete = False
        db.session.add(archive)
        db.session.commit()
        flash('已恢复')
        return redirect(url_for('.archive_recycle_bin'))
    return render_template('Archive_profile.html', archive=archive, form=form, type=1, select_main=2, select_second=3)


@main.route('/all_user', methods=['GET', 'POST'])
@admin_required
def show_all_user():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    form = SearchUserForm()
    users = User.query.filter_by()
    type = '所有用户'
    if form.validate_on_submit():
        if not form.key_words.data == '':
            if form.name.data == 'Name':
                users = User.query.filter_by(name=form.key_words.data)
            else:
                users = User.query.filter_by(email=form.key_words.data)
            type = '搜索结果'
            flash('搜索完毕,共找到' + str(users.count()) + '条结果')
        else:
            users = User.query.filter_by()
            type = '所有用户'
    return render_template('All_User.html', form=form, users=users, type=type, select_main=4)


@main.route('/user_edit_admin/<int:id>', methods=['GET', 'POST'])
@admin_required
def user_profile_edit_admin(id):
    log = Log.query.filter_by(user_id=id).count()
    user = User.query.filter_by(id=id).first()
    form = EditProfileAdminForm(user)
    if form.submit.data:
        user.email = form.email.data
        user.name = form.name.data
        user.username = form.username.data
        user.role_id = form.role.data
        user.confirmed = form.confirmed.data
        db.session.add(user)
        db.session.commit()
        flash('修改成功')
    return render_template('User_profile.html', user=user, form=form, log=log, select_main=4)


@main.route('/user_info/<int:id>', methods=['GET', 'POST'])
@login_required
def user_profile_info(id):
    if current_user.id != id and not current_user.is_administrator:
        abort(403)
    user = User.query.filter_by(id=id).first()
    form = EditProfileAdminForm(user)
    return render_template('user_profile_info.html', user=user, form=form, type=0, select_main=9, select_second=1)


@main.route('/user_edit', methods=['GET', 'POST'])
@login_required
def user_profile_edit():
    user = User.query.filter_by(id=current_user.id).first()
    form = EditProfileAdminForm(user)
    if form.submit.data:
        user.email = form.email.data
        user.name = form.name.data
        user.username = form.username.data
        db.session.add(user)
        db.session.commit()
        flash('修改成功')
    return render_template('user_profile_info.html', user=user, form=form, type=1, select_main=9,select_second=2,
                           select_third=1)


@main.route('/mail_inbox', methods=['GET', 'POST'])
@login_required
def mail_inbox():
    mails = current_user.get_mail()
    return render_template('mail_inbox.html', mails=mails, type='收件箱', select_main=10)


@main.route('/mail_send', methods=['GET', 'POST'])
@login_required
def mail_send():
    mails = current_user.get_mail_send()
    return render_template('mail_inbox.html', mails=mails, type='已发送', select_main=10)


@main.route('/mail_compose', methods=['GET', 'POST'])
@login_required
def mail_compose():
    form = ComposeMailForm()
    if current_user.is_administrator():
        if form.draft.data:
            if form.subject.data is None:
                flash('主题不能为空')
                return
            if form.receiver.data is None:
                flash('收件人不能为空')
                return
            email = Internal_mail(subject=form.subject.data,
                                  sender=current_user.id,
                                  body=form.body.data,
                                  status=2,
                                  receiver=form.receiver.data)
            db.session.add(email)
            db.session.commit()
            flash('邮件已存草稿')
            return
        if form.send.data:
            if form.subject.data is None:
                flash('主题不能为空')
                return
            if form.receiver.data is None:
                flash('收件人不能为空')
                return
            email = Internal_mail(subject=form.subject.data,
                                  body=form.body.data,
                                  status=0,
                                  sender=current_user.id,
                                  receiver=form.receiver.data)
            db.session.add(email)
            db.session.commit()
            flash('邮件已发送')
            return
    else:
        if form.draft.data:
            if form.subject.data is None:
                flash('主题不能为空')
                return
            email = Internal_mail(subject=form.subject.data,
                                  sender=current_user.id,
                                  body=form.body.data,
                                  status=2,
                                  receiver=1)
            db.session.add(email)
            db.session.commit()
            flash('邮件已存草稿')
            return
        if form.send.data:
            if form.subject.data is None:
                flash('主题不能为空')
                return
            email = Internal_mail(subject=form.subject.data,
                                  body=form.body.data,
                                  status=0,
                                  sender=current_user.id,
                                  receiver=1)
            db.session.add(email)
            db.session.commit()
            flash('邮件已发送')
            return redirect(url_for('.mail_inbox'))
    return render_template('mail_compose.html', form=form, select_main=10)


@main.route('/mail_reply/<int:receiver>', methods=['GET', 'POST'])
@admin_required
def mail_reply(receiver):
    form = ComposeMailForm()
    if form.draft.data:
        if form.subject.data is None:
            flash('主题不能为空')
            return
        if form.receiver.data is None:
            flash('收件人不能为空')
            return
        email = Internal_mail(subject=form.subject.data,
                              sender=current_user.id,
                              body=form.body.data,
                              status=2,
                              receiver=form.receiver.data)
        db.session.add(email)
        db.session.commit()
        flash('邮件已存草稿')
        return redirect(url_for('.mail_inbox'))
    if form.send.data:
        if form.subject.data is None:
            flash('主题不能为空')
            return
        if form.receiver.data is None:
            flash('收件人不能为空')
            return
        email = Internal_mail(subject=form.subject.data,
                              body=form.body.data,
                              status=0,
                              sender=current_user.id,
                              receiver=form.receiver.data)
        db.session.add(email)
        db.session.commit()
        flash('邮件已发送')
        return redirect(url_for('.mail_inbox'))
    return render_template('mail_compose.html', form=form, receiver=receiver, select_main=10)


@main.route('/mail_detail/<int:id>', methods=['GET', 'POST'])
@login_required
def mail_detail(id):
    form = DeleteForm()
    mail = Internal_mail.query.filter_by(id=id).first()
    if mail.sender != current_user.id and mail.receiver != current_user.id:
        return redirect('.mail_inbox')
    if not mail.read:
        mail.read = True
        db.session.add(mail)
        db.session.commit()
    if form.delete.data:
        if mail.sender == current_user.id:
            mail.sender_delete = True
        if mail.receiver == current_user.id:
            mail.receiver_delete = True
    return render_template('mail_detail.html', mail=mail, form=form, select_main=10)


@main.route('/mail_draft', methods=['GET', 'POST'])
@login_required
def mail_draft():
    mails = Internal_mail.query.filter_by(sender=current_user.id, status=2)
    return render_template('mail_inbox.html', mails=mails, type='草稿箱', select_main=10)


@main.route('/mail_dustbin', methods=['GET', 'POST'])
@login_required
def mail_dustbin():
    # 从草稿箱删除
    mail1 = Internal_mail.query.filter_by(sender=current_user.id, status=2)
    # 从发件箱删除
    mail2 = Internal_mail.query.filter_by(sender=current_user.id, sender_delete=True)
    # 从收件箱删除
    mail3 = Internal_mail.query.filter_by(receiver=current_user.id, receiver_delete=True)
    return render_template('mail_inbox.html', mail1=mail1, mail2=mail2, mail3=mail3, type='垃圾箱', select_main=10)


@main.route('/archive_apply', methods=['GET', 'POST'])
@login_required
def archive_apply():
    form = ArchiveApplyForm()
    if form.apply.data:
        if not form.name.data or not form.student_id or not form.reason.data:
            flash('必须填写所有信息')
            return redirect(url_for('.archive_apply'))
        archive = Archive.query.filter_by(student_id=form.student_id.data)
        if archive.count() == 0:
            flash('查无此人档案')
            return redirect(url_for('.archive_apply'))
        elif current_user.is_student() and archive.first().student_id == current_user.student_id:
            flash('别试了,这种低级错误怎么会让你通过,不能借自己档案')
            return redirect(url_for('.archive_apply'))
        elif archive.first().name != form.name.data:
            flash('验证失败,请检查输入数据')
            return redirect(url_for('.archive_apply'))
        elif form.apply_type.data == 2 and archive.first().status == 0:
            flash('档案已被借出,暂不可实体借阅')
            return redirect(url_for('.archive_apply'))
        else:
            apply = Archive_Apply(
                date=datetime.utcnow(),
                applicant=current_user.id,
                student_id=form.student_id.data,
                apply_type=form.apply_type.data,
                describe=form.reason.data,
                status=0
            )
            db.session.add(apply)
            db.session.commit()
            flash('申请提交成功')
            return redirect(url_for('.person_archive_applys'))
    return render_template('Archive_Apply.html', form=form, select_main=2, select_second=2)


@main.route('/archive_applys', methods=['GET', 'POST'])
@admin_required
def archive_applys():
    form = SearchApplicantForm()
    applys = Archive_Apply.query.filter_by()
    if form.validate_on_submit():
        if not form.key_words.data == '':
            user = User.query.filter_by(name=form.key_words.data).first()
            applys = Archive_Apply.query.filter_by(applicant=user.id)
            flash('搜索完毕,共找到' + str(applys.count()) + '条结果')
        else:
            applys = Archive_Apply.query.filter_by()
    return render_template('Archive_apply_manage.html', applys=applys, form=form, select_main=3, select_second=1)


@main.route('/archive_apply_process/<int:id>', methods=['GET', 'POST'])
@admin_required
def archive_apply_process(id):
    apply = Archive_Apply.query.filter_by(id=id).first()
    form = ArchiveApplyProcessForm()
    if form.admit.data:
        if apply.apply_type == 1:
            apply.expiry_date = datetime.utcnow().replace(day=datetime.utcnow().day + 3)
        else:
            apply.expiry_date = datetime.utcnow().replace(day=datetime.utcnow().day + 7)
        apply.status = 1
        apply.operator = current_user.id
        apply.process_date = datetime.utcnow()
        db.session.add(apply)
        db.session.commit()
        flash('已同意申请')
    elif form.forbid.data:
        if len(form.reason.data) == 0:
            flash('必须输入拒绝理由')
            return redirect(url_for('.archive_apply_process', id=id))
        apply.status = 2
        apply.forbid_reason = form.reason.data
        apply.operator = current_user.id
        apply.process_date = datetime.utcnow()
        db.session.add(apply)
        db.session.commit()
        flash('申请已拒绝')
    if form.confirm.data:
        apply.apply_taken_confirm = 1
        apply.expiry_date = set_expire_date()
        archive = Archive.query.filter_by(student_id=apply.student_id).first()
        archive.status = 0
        db.session.add(archive)
        db.session.add(apply)
        db.session.commit()
        flash('档案已被取走')
    if form.return_confirm.data:
        apply.apply_taken_confirm = 2
        archive = Archive.query.filter_by(student_id=apply.student_id).first()
        archive.status = 1
        db.session.add(apply)
        db.session.add(archive)
        db.session.commit()
        flash('还档案成功')
        return redirect(url_for('.waiting_return'))
    return render_template('Archive_apply_detail.html', apply=apply, form=form, select_main=3, select_second=1)


@main.route('/person_archive_applys', methods=['GET', 'POST'])
@login_required
def person_archive_applys():
    applys = Archive_Apply.query.filter_by(applicant=current_user.id)
    return render_template('Person_Archive_applications.html', applys=applys, select_main=2, select_second=3)


@main.route('/archive_apply_check/<int:id>', methods=['GET', 'POST'])
@login_required
def archive_apply_check(id):
    apply = Archive_Apply.query.filter_by(id=id).first()
    if apply.applicant != current_user.id:
        abort(403)
    return render_template('Archive_apply_detail_2.html', apply=apply, select_main=2, select_second=3)


@main.route('/archive_check/<int:id>', methods=['GET', 'POST'])
@login_required
def archive_check(id):
    form = ArchiveInfoForm()
    apply = Archive_Apply.query.filter_by(id=id).first()
    if apply.applicant != current_user.id or apply.status != 1 or apply.expiry:
        abort(403)
    archive = Archive.query.filter_by(student_id=apply.student_id).first()
    path = '/home/liuyu/PycharmProjects/archives_management_system/app/static/images/' + str(
        apply.student_id) + '.jpg'
    if os.path.exists(path):
        dir = 'images/' + str(apply.student_id) + '.jpg'
    else:
        dir = 'images/profile_big.jpg'
    return render_template('Archive_profile.html', archive=archive, dir=dir, form=form, select_main=2, select_second=3)


@main.route('/waiting_removed', methods=['GET', 'POST'])
@admin_required
def waiting_removed():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    form = SearchUserForm()
    applys = Archive_Apply.query.filter_by(status=1, apply_type=2, apply_taken_confirm=0)
    type = '待取走档案'
    if form.validate_on_submit():
        if not form.key_words.data == '':
            user = User.query.filter_by(name=form.key_words.data).first()
            applys = Archive_Apply.query.filter_by(status=1, apply_type=2, apply_taken_confirm=0,
                                                   applicant=user.id)
            flash('搜索完毕,共找到' + str(applys.count()) + '条结果')
        else:
            applys = Archive_Apply.query.filter_by(status=1, apply_type=2, apply_taken_confirm=0)
    return render_template('Archive_apply_manage.html', form=form, applys=applys, type=type, select_main=3,
                           select_second=2)


@main.route('/waiting_return', methods=['GET', 'POST'])
@admin_required
def waiting_return():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    form = SearchArchiveForm()
    applys = Archive_Apply.query.filter_by(status=1, apply_type=2, apply_taken_confirm=1)
    type = '待归还档案'
    if form.validate_on_submit():
        if not form.key_words.data == '':
            applys = Archive_Apply.query.filter_by(status=1, apply_type=2, apply_taken_confirm=1,
                                                   name=form.key_words.data)
            type = '搜索结果'
            flash('搜索完毕,共找到' + str(applys.count()) + '条结果')
        else:
            applys = Archive_Apply.query.filter_by(status=1, apply_type=2, apply_taken_confirm=1)
            type = '待归还档案'
    return render_template('Archive_apply_manage.html', form=form, applys=applys, type=type, view=3, select_main=3,
                           select_second=3)


archives_result = ''


@main.route('/batch_management', methods=['GET', 'POST'])
@admin_required
def batch_management():
    global archives_result
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    form = batch_managementForm()
    if form.submit.data:
        if len(form.sex.data) > 0:
            if len(form.academy.data) > 0:
                if len(form.political_status.data) > 0:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(sex=form.sex.data, academy=form.academy.data,
                                                           political_status=form.political_status.data,
                                                           grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by(sex=form.sex.data, academy=form.academy.data,
                                                           political_status=form.political_status.data)
                else:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(sex=form.sex.data, academy=form.academy.data,
                                                           grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by(sex=form.sex.data, academy=form.academy.data)
            else:
                if len(form.political_status.data) > 0:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(sex=form.sex.data,
                                                           political_status=form.political_status.data,
                                                           grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by(sex=form.sex.data,
                                                           political_status=form.political_status.data)
                else:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(sex=form.sex.data, grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by(sex=form.sex.data)
        else:
            if len(form.academy.data) > 0:
                if len(form.political_status.data) > 0:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(academy=form.academy.data,
                                                           political_status=form.political_status.data,
                                                           grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by(sex=form.sex.data, academy=form.academy.data,
                                                           political_status=form.political_status.data)
                else:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(academy=form.academy.data,
                                                           grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by(academy=form.academy.data)
            else:
                if len(form.political_status.data) > 0:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(political_status=form.political_status.data,
                                                           grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by(political_status=form.political_status.data)
                else:
                    if len(form.grade.data) > 0:
                        archives = Archive.query.filter_by(grade=form.grade.data)
                    else:
                        archives = Archive.query.filter_by()
        archives_result = archives
        flash('找到' + str(archives.count()) + '条满足条件的档案.')
        return render_template('Batch_Management.html', form=form, type='批量修改', view=1, archives=archives)
    if form.alter.data and archives_result.count() > 0:
        if len(form.political_status_2.data) > 0 and len(form.status_2.data) > 0:
            save(form.political_status_2.data, 1)
            save(form.status_2.data, 2)
        elif len(form.status_2.data) > 0 and len(form.political_status_2.data) == 0:
            save(form.status_2.data, 2)
        elif len(form.political_status_2.data) > 0 and len(form.status_2.data) == 0:
            save(form.political_status_2.data, 1)
        flash('修改成功')
    return render_template('Batch_Management.html', form=form, type='批量修改', view=0, select_main=2, select_second=4)


def save(data, type):
    global archives_result
    data.encode('utf')
    with pymysql.connect(host='localhost', user='root', password='681201', port=3306,
                         database='profiling_system', charset="utf8") as conn:
        if type == 1:
            for archive in archives_result:
                if data == '党员':
                    conn.execute("update archives set political_status = '党员' where id=" + str(archive.id))
                elif data == '共青团员':
                    conn.execute("update archives set political_status = '共青团员' where id=" + str(archive.id))
                else:
                    conn.execute("update  archives set political_status = '群众' where id=" + str(archive.id))
        elif type == 2:
            for archive in archives_result:
                if data == 0:
                    conn.execute("update archives set status = 0 where id=" + str(archive.id))
                else:
                    conn.execute("update archives set status = 1 where id=" + str(archive.id))
