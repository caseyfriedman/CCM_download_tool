import script


def test_authorExist():
    assert not script.doesAuthorExist(script.BASE_URL + "trewtwrwt")
    assert script.doesAuthorExist(script.BASE_URL + "mharford") 
    assert script.doesAuthorExist(script.BASE_URL + "mckenna-harford") 


    

