from frappe.utils.verified_command import hmac


def verify_hmac(obj, hash, key, digestmod):
    if hash == hmac.new(key.encode("utf-8"), obj, digestmod).hexdigest():
        return True
    return False
