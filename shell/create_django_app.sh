#!/bin/bash
# create_django_app.sh
# Prompt user for the app name
echo -n "Please enter your Django app name: "
read app_name

# Check if app_name is empty
if [ -z "$app_name" ]; then
    echo "App name cannot be empty!"
    exit 1
fi


# Start the Django app with the user-inputted name
python manage.py startapp $app_name

# Create directories and files for the app
mkdir $app_name/services
touch $app_name/services/__init__.py

mkdir $app_name/templates
touch $app_name/templates/__init__.py

mkdir $app_name/api
touch $app_name/api/__init__.py
touch $app_name/api/urls.py

mkdir $app_name/serializers
touch $app_name/serializers/__init__.py

mkdir $app_name/actors
touch $app_name/actors/__init__.py

mkdir $app_name/api/views
touch $app_name/api/views/__init__.py
mv $app_name/views.py $app_name/api/views

mkdir $app_name/models
touch $app_name/models/__init__.py
mv $app_name/models.py $app_name/models

mkdir $app_name/tests
mv $app_name/tests.py $app_name/tests
touch $app_name/tests/__init__.py

# Move the app to main/apps
mv $app_name main/apps

# Output success message
echo "Django app $app_name has been created and configured successfully!"

# Modify main/<app_name>/apps.py
sed -i "6s/name = '$app_name'/name = 'main.apps.$app_name'/" "main/apps/$app_name/apps.py"

# Add app to installed apps in main/settings/base.py
# This assumes that your INSTALLED_APPS section is formatted a certain way
echo "Adding $app_name to INSTALLED_APPS in main/settings/base.py"
sed -i "/INSTALLED_APPS = \[/a \    'main.apps.$app_name'," "main/settings/base.py"

# Modify main/urls.py to include the app's API URLs
# This assumes that you want to add this line at the end of the file
echo "Updating main/urls.py to include API URLs for $app_name"
# Add import statement if it doesn't exist
sed -i "s/from django.urls import path/&, include/" "main/urls.py"
# Add new path to urlpatterns
sed -i "/urlpatterns = \[/a \    path('api\/1.0\/', include('main.apps.$app_name.api.urls'))," "main/urls.py"
# Output success message
echo "Files for Django app $app_name have been modified successfully!"
