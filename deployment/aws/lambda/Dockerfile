ARG PYTHON_VERSION=3.11

FROM --platform=linux/amd64 public.ecr.aws/lambda/python:${PYTHON_VERSION}

WORKDIR /tmp

# Install system dependencies to compile (numexpr)
RUN yum install -y gcc-c++

RUN python -m pip install pip -U
RUN python -m pip install "numpy==1.26.4" "titiler.application==0.22.1" "mangum>=0.10.0" -t /asset --no-binary pydantic
RUN python -m pip install -i https://pypi.org/simple --extra-index-url https://test.pypi.org/simple "kepler-raster-server>=0.0.10" -t /asset

# Reduce package size and remove useless files
RUN cd /asset && find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[0-9]*//'); cp $f $n; done;
RUN cd /asset && find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN cd /asset && find . -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN find /asset -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN rm -rdf /asset/numpy/doc/ /asset/boto3* /asset/botocore* /asset/bin /asset/geos_license /asset/Misc

# Remove system dependencies
RUN yum remove -y gcc-c++

COPY lambda/handler.py /asset/handler.py

CMD ["echo", "hello world"]
