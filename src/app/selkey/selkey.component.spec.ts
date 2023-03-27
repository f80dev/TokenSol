import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SelkeyComponent } from './selkey.component';

describe('SelkeyComponent', () => {
  let component: SelkeyComponent;
  let fixture: ComponentFixture<SelkeyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SelkeyComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SelkeyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
