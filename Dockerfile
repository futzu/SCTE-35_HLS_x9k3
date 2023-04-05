FROM pypy:3.9-7.3.9
RUN ls /
RUN pypy3 -mpip install x9k3==0.1.89
RUN which x9k3
RUN x9k3 --version
RUN touch /sidecar.txt
#wget https://so.slo.me/longb.ts
#ADD longb.ts /longb.ts
RUN ls /
#CMD ["pypy3 x9k3"]
#start command: /opt/pypy/bin/x9k3 ...allparameters..

