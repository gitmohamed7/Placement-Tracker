"""Create fictional demo records in an empty database; never replace real records."""
from pathlib import Path
from store import Store
store=Store(Path(__file__).with_name('applications.db'))
try:
    if store.list():
        raise SystemExit('Database is not empty. No demo data added.')
    for company,role,stage,location in [
        ('Example Retail Systems','Software engineering placement','Interview','Manchester / hybrid'),
        ('Example Cloud Services','Backend developer intern','Assessment','Remote'),
        ('Example Transport Lab','Junior software placement','Applied','Salford'),
        ('Example Digital Studio','Web developer placement','Saved','Manchester')]:
        store.save({'company':company,'role':role,'stage':stage,'location':location,'notes':'Fictional demo opportunity. Replace with your own application.'})
    print('Added four fictional demo opportunities.')
finally:store.close()
