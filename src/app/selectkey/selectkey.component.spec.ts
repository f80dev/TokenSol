import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SelectkeyComponent } from './selectkey.component';

describe('SelectkeyComponent', () => {
  let component: SelectkeyComponent;
  let fixture: ComponentFixture<SelectkeyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SelectkeyComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SelectkeyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
