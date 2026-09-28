/** Own a mouse drag until release, even outside the canvas. Browser defaults
 * must not turn middle-button panning into page autoscroll on Windows. */
export function bindChartGestures(dom: HTMLElement) {
  let drag: { id: number; button: number; target: Element; x: number; y: number } | null = null;
  const wheelDuringDrag = (event: WheelEvent) => {
    if (!drag) return;
    event.preventDefault();
    event.stopPropagation(); // Panning/rotating and zooming are separate gestures.
  };
  const end = (cancel = false) => {
    const previous = drag;
    if (!previous) return;
    drag = null;
    document.removeEventListener('wheel', wheelDuringDrag, true);
    // Send the normal DOM release through zrender's event normalizer. A bare
    // internal "mouseup" lacks the coordinates needed by GL picking handlers.
    if (cancel) {
      const release = { bubbles: true, button: previous.button, buttons: 0, clientX: previous.x, clientY: previous.y };
      previous.target.dispatchEvent(new PointerEvent('pointerup', { ...release, pointerId: previous.id, pointerType: 'mouse' }));
      // zrender 5 uses mouse events on Chrome and pointer events on Edge.
      // Synthetic PointerEvents do not synthesize compatibility MouseEvents.
      previous.target.dispatchEvent(new MouseEvent('mouseup', release));
    }
    if (previous.target.hasPointerCapture(previous.id)) previous.target.releasePointerCapture(previous.id);
  };
  const down = (event: PointerEvent) => {
    // Touch/pinch remains owned by zrender; only the configured mouse buttons
    // acquire this additional browser-default guard.
    if (event.pointerType === 'touch' || ![0, 1].includes(event.button) || drag) return;
    const target = event.target;
    if (!(target instanceof Element)) return;
    drag = { id: event.pointerId, button: event.button, target, x: event.clientX, y: event.clientY };
    target.setPointerCapture(event.pointerId);
    document.addEventListener('wheel', wheelDuringDrag, { capture: true, passive: false });
  };
  const move = (event: PointerEvent) => {
    if (!drag || drag.id !== event.pointerId) return;
    drag.x = event.clientX; drag.y = event.clientY;
    const mask = drag.button === 0 ? 1 : 4;
    // Covers a release outside the browser window followed by re-entry.
    if (!(event.buttons & mask)) end(true);
  };
  const up = (event: PointerEvent) => { if (event.pointerId === drag?.id) end(); };
  const cancelled = (event: PointerEvent) => { if (event.pointerId === drag?.id) end(true); };
  const blur = () => end(true);
  const key = (event: KeyboardEvent) => { if (event.key === 'Escape') end(true); };
  const mouseDefault = (event: MouseEvent) => { if (event.button === 0 || event.button === 1) event.preventDefault(); };
  const localWheel = (event: WheelEvent) => event.preventDefault();
  dom.addEventListener('pointerdown', down);
  dom.addEventListener('lostpointercapture', cancelled);
  dom.addEventListener('mousedown', mouseDefault, true);
  dom.addEventListener('auxclick', mouseDefault);
  dom.addEventListener('wheel', localWheel, { passive: false });
  document.addEventListener('pointermove', move, true);
  document.addEventListener('pointerup', up);
  document.addEventListener('pointercancel', cancelled);
  document.addEventListener('keydown', key);
  window.addEventListener('blur', blur);
  return () => {
    end(true);
    dom.removeEventListener('pointerdown', down);
    dom.removeEventListener('lostpointercapture', cancelled);
    dom.removeEventListener('mousedown', mouseDefault, true);
    dom.removeEventListener('auxclick', mouseDefault);
    dom.removeEventListener('wheel', localWheel);
    document.removeEventListener('pointermove', move, true);
    document.removeEventListener('pointerup', up);
    document.removeEventListener('pointercancel', cancelled);
    document.removeEventListener('keydown', key);
    window.removeEventListener('blur', blur);
  };
}
