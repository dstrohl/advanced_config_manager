__author__ = 'dstrohl'


class ValidationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ValidationWarning(Warning):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ValidationsBase(object):
    """
    This is the base object that all other validation objects shoudl be based on.  it is pretty simple at this point
    and is mainly a framework for consistency.
    """

    def validate(self, data):
        """
        This is the main method for validation.  This is called by the configuration manager and the data is passed to
        it.  it should return that same data if it is validated, or raise an error or warning if not.

        Raising an error will stop the processing, raising a warning will simply log the problem, and the developer
        can choose to poll the error queue and display the errors.

        :param data:
        :return:
        """
        return data


class ValidateStrEqual(ValidationsBase):
    def __init__(self, match_str):
        self.match_str = match_str

    def validate(self, data):
        if self.match_str == data:
            return self.match_str
        else:
            raise ValidationError('ValidationError: '+self.match_str+' does not match '+data)


class ValidateStrExists(ValidationsBase):
    def validate(self, data):
        if data is not None and data != '':
            return data
        else:
            raise ValidationError('ValidationError: data cannot be empty')


class ValidateNumRange(ValidationsBase):
    def __init__(self, num_from=None, num_to=None):
        self.num_from = num_from
        self.num_to = num_to

    def validate(self, data):
        if self.num_from and data < self.num_from:
            raise ValidationError('ValidationError: '+str(data)+' is smaller than  '+str(self.num_from))

        if self.num_to and data > self.num_to:
            raise ValidationError('ValidationError: '+str(data)+' is larger than  '+str(self.num_from))

        return data

