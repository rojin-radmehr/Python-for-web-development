from flask import Blueprint
from flask import render_template,redirect,flash
from flask_login import login_user,logout_user, login_required
from app import loginform,get_user,userregistrationform,driverregistrationform,register_user,Message,app,mail,grid_fs, driver_collection


auth_blueprint = Blueprint('auth',__name__,template_folder='templates')

@auth_blueprint.route('/login',methods=['GET','POST'])
def login():
    form = loginform()
    if form.validate_on_submit():
        username = form.username.data
        pwd = form.password.data
        user = get_user(username)
        if user:
            if user.password==pwd:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect('/main')
            else:
                flash('Invalid password', 'danger')
        else:
            flash('Invalid username', 'danger')
    return render_template('login.html', form = form)

@auth_blueprint.route('/user_register', methods=['GET','POST'])
def u_register():
    form = userregistrationform()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        display_name = form.display_name.data
        role = "user"
        car = "NULL"
        if register_user(username, password, email, display_name, role,car):
            try:
                msg = Message(' Welcome to Auber - Your Registration is Complete!', sender='auber@noreply.com',recipients=[email])
                msg.html = render_template('email.html', username=username)
                mail.send(msg)
                flash('Email sent successfully!', 'success')
                
            except Exception as e:
                flash(f'Error sending email: {str(e)}', 'danger')
                
            login_user(get_user(username))
            return redirect('/main')
        else:
            flash('Invalid username', 'danger')

    return render_template('user_register.html',form=form)



@auth_blueprint.route('/driver_register', methods=['GET','POST'])
def d_register():
    form = driverregistrationform()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        display_name = form.display_name.data
        role = "driver"
        car = form.vehicle.data
        file = form.picture.data
        if register_user(username, password, email, display_name, role,car):
            try:
                msg = Message(' Welcome to Auber - Your Registration is Complete!', sender='auber@noreply.com',recipients=[email])
                msg.html = render_template('email.html', username=username)
                mail.send(msg)
                flash('Email sent successfully!', 'success')
                driver = {
                    'username': username,
                    'car': car,
                    'picture': grid_fs.put(file,filename=file.filename),
                }
                
                driver_collection.insert_one(driver)
            except Exception as e:
                flash(f'Error sending email: {str(e)}', 'danger')
                
            login_user(get_user(username))
            return redirect('/main')
        else:
            flash('Invalid username', 'danger')

    return render_template('driver_register.html',form=form)


@auth_blueprint.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect('/')



