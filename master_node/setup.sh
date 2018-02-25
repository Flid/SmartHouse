# TODO install adm
kubeadm reset
kubeadm init --config kubeadm.yaml

mkdir -p $HOME/.kube
rm -f $HOME/.kube/config
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
kubectl apply -f https://git.io/weave-kube-1.6


kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/recommended/kubernetes-dashboard.yaml


#kubectl apply -f ingress/ns-and-sa.yaml

# TODO fix certificates
#kubectl apply -f ingress/default-server-secret.yaml

#kubectl apply -f ingress/nginx-config.yaml
#kubectl apply -f ingress/nginx-deploy.yaml
#kubectl create -f ingress/setup-nodeport.yaml
