from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('metadata_mgt', '0009_agent_conversation_f_agent_uid'),
    ]

    operations = [
        migrations.CreateModel(
            name='Audio',
            fields=[
                ('audio_id', models.AutoField(primary_key=True, serialize=False)),
                ('audio_uid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('audio_path', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('f_conversation_uid', models.ForeignKey(db_column='f_conversation_uid', on_delete=django.db.models.deletion.CASCADE, to='metadata_mgt.conversation', to_field='conversation_uid')),
            ],
            options={
                'db_table': 'audio',
            },
        ),
    ]
