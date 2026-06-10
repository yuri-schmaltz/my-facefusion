#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Iniciar o backend no segundo plano
"$DIR/facefusion-app" &
BACKEND_PID=$!

echo "Inicializando o FaceFusion local..."
# Aguardar inicializacao
PORT=8000
for i in {1..20}; do
    for p in {8000..8020}; do
        if curl -s http://localhost:$p/api/config > /dev/null; then
            PORT=$p
            break 2
        fi
    done
    sleep 0.5
done

URL="http://localhost:${PORT}/"
echo "Abrindo o navegador em $URL"

if which xdg-open > /dev/null; then
    xdg-open "$URL"
elif which gnome-open > /dev/null; then
    gnome-open "$URL"
elif which kde-open > /dev/null; then
    kde-open "$URL"
else
    echo "Abra o navegador em: $URL"
fi

# Aguardar finalizacao do backend
wait $BACKEND_PID
