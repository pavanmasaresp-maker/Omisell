# OmniSell Phase 4 overlay: publish + inventory sync
Apply on top of your repo (Phase 1 + 2a + Orders):
  cd backend
  python manage.py makemigrations marketplaces
  python manage.py migrate
  python manage.py test
  python manage.py run_sync_worker        # alag terminal mein, chalta rehna chahiye
