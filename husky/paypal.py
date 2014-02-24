import os
import urllib, urllib2
import json as simplejson

from M2Crypto import BIO, SMIME, X509

from django.conf import settings

import logging
logger = logging.getLogger(__name__)

cwd = os.path.dirname(os.path.realpath(__file__))
PAYPAL_PAYPAL_CERT = os.path.join(cwd, settings.PAYPAL_PAYPAL_CERT)
PAYPAL_PRIVATE_KEY = os.path.join(cwd, settings.PAYPAL_PRIVATE_KEY)
PAYPAL_PUBLIC_KEY = os.path.join(cwd, settings.PAYPAL_PUBLIC_KEY)

# Django and PayPal payment processing
# http://fortylines.com/blog/djangoPaypalIntegration.blog.html
# https://developer.paypal.com/webapps/developer/docs/classic/paypal-payments-standard/integration-guide/encryptedwebpayments/
# 
# $ openssl genrsa -out hostname-paypal-priv.pem 1024
# $ openssl req -new -key hostname-paypal-priv.pem -x509 \
#           -days 365 -out hostname-paypal-pubcert.pem
# 
# Useful command to check certificate expiration
# $ openssl x509 -in hostname-paypal-pubcert.pem -noout -enddate

class PayPalError(Exception):
    '''Base class for PayPal errors'''

    @property
    def message(self, message=''):
        '''Returns the first argument used to construct this error.'''
        return message

class PayPal(object):

    def encrypt(self, attributes):
        plaintext = ''

        for key, value in attributes.items():
            plaintext += u'%s=%s\n' % (key, value)

        plaintext = plaintext.encode('utf-8')

        # Instantiate an SMIME object.
        s = SMIME.SMIME()

        # Load signer's key and cert. Sign the buffer.
        s.load_key_bio(BIO.openfile(PAYPAL_PRIVATE_KEY), BIO.openfile(PAYPAL_PUBLIC_KEY))

        p7 = s.sign(BIO.MemoryBuffer(plaintext), flags=SMIME.PKCS7_BINARY)

        # Load target cert to encrypt the signed message to.
        x509 = X509.load_cert_bio(BIO.openfile(PAYPAL_PAYPAL_CERT))
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)

        # Set cipher: 3-key triple-DES in CBC mode.
        s.set_cipher(SMIME.Cipher('des_ede3_cbc'))

        # Create a temporary buffer.
        tmp = BIO.MemoryBuffer()

        # Write the signed message into the temporary buffer.
        p7.write_der(tmp)

        # Encrypt the temporary buffer.
        p7 = s.encrypt(tmp, flags=SMIME.PKCS7_BINARY)

        # Output p7 in mail-friendly format.
        out = BIO.MemoryBuffer()
        p7.write(out)

        return out.read()

    def download_csv(self, start_date=None, end_date=None):
        try:
            results = getHttpRequest(settings.PAYPAL_IPN_URL, 'cmd=TransactionSearch&STARTDATE=%s&ENDDATE=%s' % (start_date, end_date))
        except Exception, e:
            print 'Failed to Download Transactions'
        return results

    def create_payment(self, data=None):
        code, content = self._makeRequest(data)
#         print '==== content [%s][%s]'%(code, content)
        resopnse = simplejson.loads(content)
#         print '==== resopnse [%s]'%(resopnse)
        if resopnse['state'] == 'approved':
            self.finalize_payment(resopnse['links'][0]['href'], resopnse['id'])
            # redirect to thank you page and mark as paid
#             print '==== content [%s][%s]'%(code, content)

    def finalize_payment(self, uri=None, id=None):
        data = simplejson.dumps({'payer_id': id})
        request = urllib2.Request('%s/execute'%(uri), data)
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', 'Bearer %s' % (settings.PAYPAL_REST_API_ACCESS_TOKEN))
        try:
            response = urllib2.urlopen(request)
            code     = response.code
            content  = response.read()
        except urllib2.URLError, e:
            print 'Failed to send Final PayPal Payment request'
            raise urllib2.URLError, e
            sys.exit()
        return code, content

    def _makeRequest(self, data=None):
        if not data: return
        """ sends data to the PayPal API """
        uri = '%s/v1/payments/payment' % (settings.PAYPAL_REST_API_ENDPOINT)
#         print '==== data [%s]'%(data)
#         print '==== uri [%s]'%(uri)
        data = simplejson.dumps(data)
        request = urllib2.Request(uri, data)
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', 'Bearer %s' % (settings.PAYPAL_REST_API_ACCESS_TOKEN))
        try:
            response = urllib2.urlopen(request)
            code     = response.code
            content  = response.read()
        except urllib2.URLError, e:
            print 'Failed to send PayPal Payment data'
            raise urllib2.URLError, e
            sys.exit()
        return code, content

if __name__ == '__main__':
    params = {
      'intent': 'sale',
#       'redirect_urls': 'http://dev.husky-hustle.com/thank-you?payer_id=',
#       'redirect_urls': 'http://%s/thank-you?payer_id=' % (site.domain),
#       'notify_url': 'http://%s/paid/%s' % (site.domain, ids),
      'payer': {
        'payment_method': 'credit_card',
        'funding_instruments': [
          {
            'credit_card': {
              'number': '4417119669820331',
              'type': 'visa',
              'expire_month': 11,
              'expire_year': 2018,
              'cvv2': '874',
              'first_name': 'Betsy',
              'last_name': 'Buyer',
              'billing_address': {
                'line1': '111 First Street',
                'city': 'Saratoga',
                'state': 'CA',
                'postal_code': '95070',
                'country_code': 'US'
              }
            }
          }
        ]
      },
      'transactions': [
        {
          'amount': {
            'total': '7.47',
            'currency': 'USD',
            'details': {
              'subtotal': '7.41',
              'tax': '0.03',
              'shipping': '0.03'
            }
          },
          'description': 'This is the payment transaction description.'
        }
      ]
    }
    PayPal().create_payment(params)
