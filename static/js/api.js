export async function getState() {
    return (await fetch("/state")).json();
}

export async function postStep() {
    return (await fetch("/step", { method: "POST" })).json();
}

export async function postReset() {
    return (await fetch("/reset", { method: "POST" })).json();
}
