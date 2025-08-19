import script


def test_authorExist():
    assert not script.doesAuthorExist('https://coloradocommunitymedia.com/author/' + "trewtwrwt")
    assert script.doesAuthorExist('https://coloradocommunitymedia.com/author/' + "mharford") 
    assert script.doesAuthorExist('https://coloradocommunitymedia.com/author/' + "mckenna-harford") 


    

def test_getAllArticles():
    total = script.calculate_total_articles('https://coloradocommunitymedia.com/author/', authors = ["tiojiodfsa", "jfdasiofas"])
    assert len(total) == 0
    total = script.calculate_total_articles('https://coloradocommunitymedia.com/author/', authors = ["mckenna-harford"])
    print(f"mckenna-harford has {len(total)}")

