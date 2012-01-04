from google.appengine.ext import db
from lp.model import Archive
from lp.model import Tag

def get_by_query(query):
    
    if type == "archive":
        cls = Archive
    elif type == "tag":
        cls = Tag
    
    q = cls.all()
    
    if 'order' in query:
        q.order(query['order'])
    else:
        q.order("-key_name")
        
    if 'limit' in query:
        limit = query['limit']
    else:
        limit = 1000 #TODO: GAE has removed the 1000 limit, consider revising.
    
    results = q.fetch(limit)
    
    return results

def update_count(type, add = [], subtract = []):
    #input: type = "archive" or "tag"; add, subtract = e.g. ["200412","200501"] or ["Books", "Games"]
    
    if type == "archive":
        cls = Archive
    elif type == "tag":
        cls = Tag
    
    items_dict = {}
    for t in add:
        if t in items_dict:
            items_dict[t] += 1
        else:
            items_dict[t] = 1
    for t in subtract:
        if t in items_dict:
            items_dict[t] -= 1
        else:
            items_dict[t] = -1
    for k in items_dict.keys(): # No need to modify if the count change to a term is 0.
        if items_dict[k] == 0:
            items_dict.pop(k)
    
    results = cls.get_by_key_name(items_dict.keys())
    
    # cls.get_by_key_name returns a quirky [ None, ] when no result can be found.
    results = filter(lambda a: a != None, results)
    
    to_add = []
    to_del = []
    
    if results:
        
        i = 0
        while i < len(results):
            results[i].count += items_dict[results[i].key().name()]
            items_dict.pop(results[i].key().name())
            #pop out terms found in query results so the rest will be new terms.
            if results[i].count < 1:
                to_del.append(results[i])
                results.pop(i)
            else:
                i += 1
        """
        for i in range(len(results)):
            results[i].count += items_dict[results[i].key().name()]
            items_dict.pop(results[i].key().name())
            #pop out terms found in query results so the rest will be new terms.
            if results[i].count < 1:
                to_del.append(results[i])
                results.pop(i)
                i -= 1
        """
    # create new entries for non-existing terms
    if len(items_dict) > 0:
        for t in items_dict:
            if items_dict[t] > 0:
                # Don't create new term unless the initial count > 0
                to_add.append(cls(key_name = t, count = items_dict[t]))
        results += to_add
    
    db.put(results)
    
    # remove terms whose count < 1
    if len(to_del) > 0:
        db.delete(to_del)